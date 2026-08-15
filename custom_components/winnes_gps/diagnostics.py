"""Privacy-preserving diagnostics for WINNES GPS."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, CONF_USER_ID
from .coordinator import WinnesConfigEntry

CONFIG_FIELDS_TO_REDACT = {CONF_USER_ID, CONF_DEVICE_ID}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: WinnesConfigEntry
) -> dict[str, Any]:
    """Return diagnostics without coordinates, IDs or tracker-identifying data."""

    coordinator = config_entry.runtime_data.coordinator
    data = coordinator.data

    safe_data: dict[str, Any] | None = None
    if data is not None:
        # Deliberately report capabilities/presence rather than telemetry values.
        # Exact coordinates, timestamps, speed, distance, device name and backend
        # identifiers are not included in diagnostics at all.
        safe_data = {
            "privacy_mode": data.privacy_mode,
            "model": data.model,
            "model_name": data.model_name,
            "backend_status": data.normalized_status,
            "position_source": data.position_source,
            "has_location": data.latitude is not None and data.longitude is not None,
            "has_battery": data.battery_percent is not None,
            "has_speed": data.speed_kmh is not None,
            "has_device_timestamp": data.device_time is not None,
            "has_server_timestamp": data.server_time is not None,
        }

    return {
        "config_entry": async_redact_data(
            dict(config_entry.data), CONFIG_FIELDS_TO_REDACT
        ),
        "options": dict(config_entry.options),
        "last_update_success": coordinator.last_update_success,
        "data": safe_data,
    }
