"""Binary sensor platform for WINNES GPS."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WinnesConfigEntry, WinnesDataUpdateCoordinator
from .entity import WinnesCoordinatorEntity
from .model import WinnesDeviceData


@dataclass(frozen=True, kw_only=True)
class WinnesBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe one WINNES binary sensor."""

    value_fn: Callable[[WinnesDeviceData], bool | None]


BINARY_SENSORS: tuple[WinnesBinarySensorEntityDescription, ...] = (
    WinnesBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data.is_online,
    ),
    WinnesBinarySensorEntityDescription(
        key="moving",
        translation_key="moving",
        device_class=BinarySensorDeviceClass.MOVING,
        value_fn=lambda data: data.is_moving,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WinnesConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WINNES GPS binary sensors."""

    coordinator = config_entry.runtime_data.coordinator
    async_add_entities(
        WinnesBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class WinnesBinarySensor(WinnesCoordinatorEntity, BinarySensorEntity):
    """Represent a WINNES binary state."""

    entity_description: WinnesBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: WinnesDataUpdateCoordinator,
        description: WinnesBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, key=description.key)
        self.entity_description = description

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the binary state."""

        data = self.coordinator.data
        if data is None or data.privacy_mode:
            return None
        return self.entity_description.value_fn(data)

    @property
    @override
    def available(self) -> bool:
        """Return unavailable if the backend did not provide this state."""

        return super().available and self.is_on is not None
