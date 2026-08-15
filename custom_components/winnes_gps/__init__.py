"""WINNES GPS integration for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WinnesApi
from .const import (
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    CONF_USER_ID,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
)
from .coordinator import WinnesConfigEntry, WinnesDataUpdateCoordinator, WinnesRuntimeData


async def async_setup_entry(hass: HomeAssistant, entry: WinnesConfigEntry) -> bool:
    """Set up WINNES GPS from a config entry."""

    api = WinnesApi(
        async_get_clientsession(hass),
        user_id=int(entry.data[CONF_USER_ID]),
        device_id=int(entry.data[CONF_DEVICE_ID]),
    )
    scan_interval = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    coordinator = WinnesDataUpdateCoordinator(
        hass,
        entry,
        api=api,
        scan_interval=scan_interval,
    )
    entry.runtime_data = WinnesRuntimeData(api=api, coordinator=coordinator)

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a WINNES GPS config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
