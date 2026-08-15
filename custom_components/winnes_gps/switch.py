"""Privacy switch platform for WINNES GPS."""

from __future__ import annotations

from typing import override

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_PRIVACY_MODE
from .coordinator import WinnesConfigEntry, WinnesDataUpdateCoordinator
from .entity import WinnesCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WinnesConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the WINNES privacy switch."""

    async_add_entities(
        [
            WinnesPrivacySwitch(
                config_entry.runtime_data.coordinator,
                config_entry,
            )
        ]
    )


class WinnesPrivacySwitch(WinnesCoordinatorEntity, SwitchEntity):
    """Persistently disable all WINNES polling and clear live telemetry."""

    _attr_translation_key = "privacy_mode"
    _attr_icon = "mdi:shield-lock-outline"

    def __init__(
        self,
        coordinator: WinnesDataUpdateCoordinator,
        config_entry: WinnesConfigEntry,
    ) -> None:
        super().__init__(coordinator, key="privacy_mode")
        self._config_entry = config_entry

    @property
    @override
    def is_on(self) -> bool:
        """Return whether privacy mode is active."""

        return self.coordinator.privacy_mode

    @property
    @override
    def available(self) -> bool:
        """Privacy control remains available even during backend outages."""

        return True

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable fail-closed privacy mode."""

        self._persist(True)
        await self.coordinator.async_set_privacy(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable privacy mode and immediately request fresh telemetry."""

        self._persist(False)
        await self.coordinator.async_set_privacy(False)

    def _persist(self, enabled: bool) -> None:
        """Persist the privacy state across Home Assistant restarts."""

        options = dict(self._config_entry.options)
        options[CONF_PRIVACY_MODE] = enabled
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            options=options,
        )
