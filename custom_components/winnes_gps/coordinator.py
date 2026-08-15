"""Data update coordinator for WINNES GPS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    WinnesApi,
    WinnesCannotConnect,
    WinnesDeviceNotFound,
    WinnesInvalidResponse,
)
from .const import CONF_PRIVACY_MODE, DEFAULT_SCAN_INTERVAL, NAME
from .model import WinnesDeviceData

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class WinnesRuntimeData:
    """Runtime objects for one config entry."""

    api: WinnesApi
    coordinator: "WinnesDataUpdateCoordinator"


type WinnesConfigEntry = ConfigEntry[WinnesRuntimeData]


class WinnesDataUpdateCoordinator(DataUpdateCoordinator[WinnesDeviceData]):
    """Manage polling and fail-closed privacy state."""

    config_entry: WinnesConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: WinnesConfigEntry,
        *,
        api: WinnesApi,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=NAME,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.privacy_mode = bool(config_entry.options.get(CONF_PRIVACY_MODE, False))

    async def _async_update_data(self) -> WinnesDeviceData:
        """Fetch current data unless privacy mode is active."""

        if self.privacy_mode:
            # Important privacy invariant: no HTTP request is made on this path.
            return self.api.private_data()

        try:
            data = await self.api.async_get_device(timezone_offset(self.hass))
            # If privacy was enabled while an already-running request was in
            # flight, discard that response before it can reach entity state.
            if self.privacy_mode:
                return self.api.private_data()
            return data
        except WinnesDeviceNotFound as err:
            raise UpdateFailed("Configured WINNES device was not returned") from err
        except WinnesInvalidResponse as err:
            raise UpdateFailed("WINNES returned an invalid response") from err
        except WinnesCannotConnect as err:
            raise UpdateFailed("Unable to reach WINNES") from err

    async def async_set_privacy(self, enabled: bool) -> None:
        """Apply privacy mode immediately and refresh entity states."""

        self.privacy_mode = enabled
        if enabled:
            # Clear published telemetry synchronously. Any in-flight request is
            # also discarded by _async_update_data before listeners are updated.
            self.async_set_updated_data(self.api.private_data())
            return
        await self.async_request_refresh()


def timezone_offset(hass: HomeAssistant) -> str:
    """Return the current Home Assistant timezone offset in WINNES format."""

    try:
        local_now = datetime.now(ZoneInfo(hass.config.time_zone))
    except Exception:  # ZoneInfo data is normally guaranteed by Home Assistant.
        local_now = datetime.now().astimezone()
    offset = local_now.utcoffset() or timedelta(0)
    total_minutes = int(offset.total_seconds() // 60)
    sign = "-" if total_minutes < 0 else ""
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours}:{minutes:02d}"
