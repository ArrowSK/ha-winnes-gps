"""Shared entity helpers for WINNES GPS."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MONITOR_URL
from .coordinator import WinnesDataUpdateCoordinator


class WinnesCoordinatorEntity(CoordinatorEntity[WinnesDataUpdateCoordinator]):
    """Base coordinator entity for one WINNES tracker."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WinnesDataUpdateCoordinator,
        *,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.api.local_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the Home Assistant device registry information."""

        data = self.coordinator.data
        name = data.name if data and data.name else "WINNES GPS tracker"
        model = None
        if data:
            model = data.model_name or data.model
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.api.local_id)},
            name=name,
            manufacturer="WINNES / TKSTAR",
            model=model,
            configuration_url=MONITOR_URL,
        )

    @property
    def available(self) -> bool:
        """Return entity availability, hiding telemetry in privacy mode."""

        data = self.coordinator.data
        return bool(
            super().available
            and data is not None
            and not data.privacy_mode
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return no shared attributes by default."""

        return None
