"""Minimal async client for the WINNES/mytkstar tracking backend."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from hashlib import sha256
from typing import Any

import aiohttp

from .const import BASE_URL, DEVICE_ENDPOINT, MONITOR_URL, REQUEST_TIMEOUT
from .model import WinnesDeviceData, WinnesPayloadError, parse_legacy_devices


class WinnesApiError(Exception):
    """Base class for WINNES API errors."""


class WinnesCannotConnect(WinnesApiError):
    """Raised when the backend cannot be reached."""


class WinnesInvalidResponse(WinnesApiError):
    """Raised when the backend returns an unexpected response."""


class WinnesDeviceNotFound(WinnesApiError):
    """Raised when the requested backend device is not returned."""


class WinnesApi:
    """Small client that performs only the polling call required by Home Assistant."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        user_id: int,
        device_id: int,
    ) -> None:
        self._session = session
        self.user_id = user_id
        self.device_id = device_id
        self.local_id = sha256(
            f"{self.user_id}:{self.device_id}".encode("ascii")
        ).hexdigest()[:32]
        self._first_request = True
        self._metadata: dict[str, Any] = {}

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Return the non-location metadata learned on the first successful poll."""

        return self._metadata

    def private_data(self) -> WinnesDeviceData:
        """Return a telemetry-free state for privacy mode."""

        return WinnesDeviceData.private(
            self.device_id,
            name=self._metadata.get("name"),
            model=self._metadata.get("model"),
            model_name=self._metadata.get("modelName"),
        )

    async def async_get_device(self, timezone_offset: str) -> WinnesDeviceData:
        """Fetch and normalize one tracker state."""

        if not _valid_timezone_offset(timezone_offset):
            raise WinnesInvalidResponse("Invalid timezone offset")

        # The legacy ASP.NET endpoint expects the same JavaScript-style body used
        # by the official web client, despite advertising application/json.
        body = (
            "{UserID:"
            f"{self.user_id},"
            f"isFirst:{str(self._first_request).lower()},"
            f"TimeZones:'{timezone_offset}',"
            f"DeviceID:{self.device_id},"
            "IsKM:1}"
        )
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": BASE_URL,
            "Referer": MONITOR_URL,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "HomeAssistant-WINNES-GPS/0.1",
        }

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.post(
                    DEVICE_ENDPOINT,
                    data=body,
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        raise WinnesCannotConnect(
                            f"WINNES backend returned HTTP {response.status}"
                        )
                    envelope = await response.json(content_type=None)
        except TimeoutError as err:
            raise WinnesCannotConnect("Timed out contacting WINNES") from err
        except aiohttp.ClientError as err:
            raise WinnesCannotConnect("Could not contact WINNES") from err
        except ValueError as err:
            raise WinnesInvalidResponse("WINNES returned non-JSON data") from err

        if not isinstance(envelope, dict) or not isinstance(envelope.get("d"), str):
            raise WinnesInvalidResponse("WINNES response envelope is invalid")

        try:
            devices = parse_legacy_devices(envelope["d"])
        except WinnesPayloadError as err:
            raise WinnesInvalidResponse("WINNES device payload is invalid") from err

        raw = next(
            (
                item
                for item in devices
                if _safe_int(item.get("id")) == self.device_id
            ),
            None,
        )
        if raw is None:
            raise WinnesDeviceNotFound("Requested WINNES device was not returned")

        if self._first_request:
            # Intentionally retain only non-location, non-registration metadata.
            # Do not persist serial number, car registration, coordinates or other
            # sensitive fields that the first response may contain.
            for key in ("name", "model", "modelName", "icon"):
                if raw.get(key) not in (None, ""):
                    self._metadata[key] = raw[key]
            self._first_request = False

        return WinnesDeviceData.from_raw(
            raw,
            backend_device_id=self.device_id,
            metadata=dict(self._metadata),
        )


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _valid_timezone_offset(value: str) -> bool:
    """Validate the small offset string interpolated into the legacy request body."""

    if not value or len(value) > 6 or ":" not in value:
        return False
    hours_text, minutes_text = value.rsplit(":", 1)
    if hours_text.startswith("-"):
        hours_text = hours_text[1:]
    if not hours_text.isdigit() or not minutes_text.isdigit():
        return False
    hours = int(hours_text)
    minutes = int(minutes_text)
    return 0 <= hours <= 14 and 0 <= minutes <= 59
