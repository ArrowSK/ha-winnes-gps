"""Device tracker platform for WINNES GPS."""

from __future__ import annotations

from typing import Any, override

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WinnesConfigEntry, WinnesDataUpdateCoordinator
from .entity import WinnesCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WinnesConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the WINNES GPS device tracker."""

    async_add_entities(
        [WinnesDeviceTracker(config_entry.runtime_data.coordinator)]
    )


class WinnesDeviceTracker(WinnesCoordinatorEntity, TrackerEntity):
    """Represent the current tracker location."""

    _attr_translation_key = "location"
    _attr_name = None

    def __init__(self, coordinator: WinnesDataUpdateCoordinator) -> None:
        super().__init__(coordinator, key="location")

    @property
    @override
    def latitude(self) -> float | None:
        """Return latitude."""

        data = self.coordinator.data
        return data.latitude if data and not data.privacy_mode else None

    @property
    @override
    def longitude(self) -> float | None:
        """Return longitude."""

        data = self.coordinator.data
        return data.longitude if data and not data.privacy_mode else None

    @property
    @override
    def available(self) -> bool:
        """Return availability only when a live coordinate exists."""

        data = self.coordinator.data
        return bool(
            super().available
            and data is not None
            and data.latitude is not None
            and data.longitude is not None
        )

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose non-secret location metadata useful in automations."""

        data = self.coordinator.data
        if data is None or data.privacy_mode:
            return None
        return {
            "position_timestamp": data.device_time,
            "position_source": data.position_source,
            "speed_kmh": data.speed_kmh,
            "course_degrees": data.course_degrees,
            "tracker_status": data.normalized_status,
        }
