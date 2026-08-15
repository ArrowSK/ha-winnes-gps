"""Sensor platform for WINNES GPS."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WinnesConfigEntry, WinnesDataUpdateCoordinator
from .entity import WinnesCoordinatorEntity
from .model import WinnesDeviceData

SensorValue = int | float | str | datetime | None


@dataclass(frozen=True, kw_only=True)
class WinnesSensorEntityDescription(SensorEntityDescription):
    """Describe one WINNES sensor."""

    value_fn: Callable[[WinnesDeviceData], SensorValue]


SENSORS: tuple[WinnesSensorEntityDescription, ...] = (
    WinnesSensorEntityDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.battery_percent,
    ),
    WinnesSensorEntityDescription(
        key="speed",
        translation_key="speed",
        device_class=SensorDeviceClass.SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.speed_kmh,
    ),
    WinnesSensorEntityDescription(
        key="last_position",
        translation_key="last_position",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.device_time,
    ),
    WinnesSensorEntityDescription(
        key="position_source",
        translation_key="position_source",
        icon="mdi:crosshairs-gps",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.position_source,
    ),
    WinnesSensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:car-info",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.normalized_status,
    ),
    WinnesSensorEntityDescription(
        key="distance",
        translation_key="distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.total_distance_km,
    ),
    WinnesSensorEntityDescription(
        key="course",
        translation_key="course",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.course_degrees,
    ),
    WinnesSensorEntityDescription(
        key="stop_duration",
        translation_key="stop_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.stop_minutes if data.is_stopped else None,
    ),
    WinnesSensorEntityDescription(
        key="offline_duration",
        translation_key="offline_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.offline_minutes if data.is_online is False else None,
    ),
    WinnesSensorEntityDescription(
        key="server_update",
        translation_key="server_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.server_time,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WinnesConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WINNES GPS sensors."""

    coordinator = config_entry.runtime_data.coordinator
    async_add_entities(
        WinnesSensor(coordinator, description) for description in SENSORS
    )


class WinnesSensor(WinnesCoordinatorEntity, SensorEntity):
    """Represent one normalized WINNES value."""

    entity_description: WinnesSensorEntityDescription

    def __init__(
        self,
        coordinator: WinnesDataUpdateCoordinator,
        description: WinnesSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, key=description.key)
        self.entity_description = description

    @property
    @override
    def native_value(self) -> Any:
        """Return the sensor value."""

        data = self.coordinator.data
        if data is None or data.privacy_mode:
            return None
        return self.entity_description.value_fn(data)

    @property
    @override
    def available(self) -> bool:
        """Return unavailable when privacy is active or this value is absent."""

        return super().available and self.native_value is not None
