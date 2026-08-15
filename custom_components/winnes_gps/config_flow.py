"""Config flow for WINNES GPS."""

from __future__ import annotations

import logging
from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    WinnesApi,
    WinnesCannotConnect,
    WinnesDeviceNotFound,
    WinnesInvalidResponse,
)
from .const import (
    CONF_DEVICE_ID,
    CONF_PRIVACY_MODE,
    CONF_SCAN_INTERVAL,
    CONF_USER_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import timezone_offset

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USER_ID): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Required(CONF_DEVICE_ID): vol.All(vol.Coerce(int), vol.Range(min=1)),
    }
)


class WinnesGpsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WINNES GPS."""

    VERSION = 1

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: Any) -> "WinnesGpsOptionsFlow":
        """Return the options flow."""

        return WinnesGpsOptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Set up a tracker using the backend IDs visible in the web request."""

        errors: dict[str, str] = {}

        if user_input is not None:
            user_id = int(user_input[CONF_USER_ID])
            device_id = int(user_input[CONF_DEVICE_ID])

            api = WinnesApi(
                async_get_clientsession(self.hass),
                user_id=user_id,
                device_id=device_id,
            )
            await self.async_set_unique_id(api.local_id)
            self._abort_if_unique_id_configured()

            try:
                data = await api.async_get_device(timezone_offset(self.hass))
            except WinnesDeviceNotFound:
                errors["base"] = "device_not_found"
            except WinnesCannotConnect:
                errors["base"] = "cannot_connect"
            except WinnesInvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:  # noqa: BLE001 - prevent secrets leaking in flow errors
                _LOGGER.exception("Unexpected error validating WINNES configuration")
                errors["base"] = "unknown"
            else:
                title = data.name or data.model_name or "WINNES GPS tracker"
                return self.async_create_entry(
                    title=title,
                    data={CONF_USER_ID: user_id, CONF_DEVICE_ID: device_id},
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_PRIVACY_MODE: False,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )


class WinnesGpsOptionsFlow(OptionsFlowWithReload):
    """Manage WINNES GPS options."""

    @override
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage polling and startup privacy settings."""

        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    CONF_PRIVACY_MODE: bool(user_input[CONF_PRIVACY_MODE]),
                }
            )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=int(
                        self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        )
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
                vol.Optional(
                    CONF_PRIVACY_MODE,
                    default=bool(
                        self.config_entry.options.get(CONF_PRIVACY_MODE, False)
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
