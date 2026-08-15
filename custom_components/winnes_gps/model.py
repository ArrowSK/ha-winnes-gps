"""Data model and legacy response parser for WINNES GPS.

This module intentionally uses only the Python standard library so its parser can
be unit-tested without Home Assistant installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from typing import Any


class WinnesPayloadError(ValueError):
    """Raised when the legacy WINNES payload cannot be parsed."""


def _quote_unquoted_keys(text: str) -> str:
    """Convert a JavaScript-style object literal to JSON without executing it.

    WINNES returns an ASP.NET JSON envelope whose ``d`` value contains a legacy
    JavaScript object literal such as ``{devices:[{id:1,name:\"Tracker\"}]}``.
    The object keys are unquoted, so the inner value is not valid JSON.

    This scanner quotes keys only while outside string literals. It deliberately
    does not use eval/exec or a JavaScript engine.
    """

    out: list[str] = []
    i = 0
    length = len(text)
    in_string = False
    quote = ""
    escaped = False
    expect_key = False

    while i < length:
        char = text[i]

        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_string = False
            i += 1
            continue

        if char in {'"', "'"}:
            # The observed server responses use JSON-compatible double-quoted
            # strings. Refuse single-quoted response strings rather than trying
            # to guess JavaScript escaping semantics.
            if char == "'":
                raise WinnesPayloadError("Unsupported single-quoted response string")
            in_string = True
            quote = char
            out.append(char)
            i += 1
            continue

        if char in "{,":
            out.append(char)
            expect_key = True
            i += 1
            continue

        if expect_key:
            if char.isspace():
                out.append(char)
                i += 1
                continue

            if char.isalpha() or char == "_":
                start = i
                i += 1
                while i < length and (text[i].isalnum() or text[i] == "_"):
                    i += 1
                key = text[start:i]
                whitespace_start = i
                while i < length and text[i].isspace():
                    i += 1
                if i < length and text[i] == ":":
                    out.append(json.dumps(key))
                    out.append(text[whitespace_start:i])
                    out.append(":")
                    i += 1
                    expect_key = False
                    continue
                out.append(key)
                expect_key = False
                continue

            expect_key = False

        out.append(char)
        i += 1

    if in_string:
        raise WinnesPayloadError("Unterminated response string")

    return "".join(out)


def parse_legacy_devices(payload: str) -> list[dict[str, Any]]:
    """Parse the legacy ``d`` response and return its device objects."""

    if not isinstance(payload, str) or not payload.strip():
        raise WinnesPayloadError("Empty device payload")

    try:
        parsed = json.loads(_quote_unquoted_keys(payload))
    except (json.JSONDecodeError, WinnesPayloadError) as err:
        if isinstance(err, WinnesPayloadError):
            raise
        raise WinnesPayloadError("Malformed device payload") from err

    if not isinstance(parsed, dict):
        raise WinnesPayloadError("Device payload is not an object")

    devices = parsed.get("devices")
    if not isinstance(devices, list):
        raise WinnesPayloadError("Device payload has no devices list")

    return [item for item in devices if isinstance(item, dict)]


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_bool_from_int(value: Any) -> bool | None:
    parsed = _as_int(value)
    if parsed is None:
        return None
    if parsed == 1:
        return True
    if parsed == 0:
        return False
    return None


def _as_utc_datetime(value: Any) -> datetime | None:
    """Parse the UTC timestamps emitted by the WINNES backend."""

    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(candidate, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def decode_battery_percent(model: str | None, data_context: Any) -> int | None:
    """Decode battery percentage for known WINNES/TKSTAR model families.

    The current web client decodes TK915/model 152 and closely related tracker
    models from the second dash-separated field. Unknown models deliberately
    return ``None`` instead of guessing.
    """

    if model is None or data_context in (None, ""):
        return None

    text = str(data_context).strip()
    model_text = str(model).strip()

    if model_text in {"1500", "1501"}:
        candidate = text
    elif model_text == "194":
        parts = text.split("$")
        candidate = parts[1] if len(parts) >= 2 else ""
    elif model_text in {
        "150",
        "151",
        "152",
        "153",
        "154",
        "155",
        "156",
        "158",
        "159",
        "180",
        "181",
        "182",
        "183",
        "184",
        "185",
        "186",
        "187",
        "188",
        "189",
    }:
        parts = text.split("-")
        candidate = parts[1] if len(parts) >= 2 else ""
    else:
        return None

    percent = _as_int(candidate)
    if percent is None or not 0 <= percent <= 100:
        return None
    return percent


def normalize_position_source(value: Any) -> str | None:
    """Map the backend positioning type to a readable value."""

    mapping = {"1": "GPS", "2": "LBS", "3": "Wi-Fi"}
    if value in (None, ""):
        return None
    return mapping.get(str(value), "Unknown")


@dataclass(slots=True, frozen=True)
class WinnesDeviceData:
    """Normalized WINNES tracker state."""

    backend_device_id: int
    name: str | None = None
    model: str | None = None
    model_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    server_time: datetime | None = None
    device_time: datetime | None = None
    speed_kmh: float | None = None
    course_degrees: float | None = None
    position_source: str | None = None
    total_distance_km: float | None = None
    is_stopped: bool | None = None
    stop_minutes: int | None = None
    offline_minutes: int | None = None
    backend_status: str | None = None
    battery_percent: int | None = None
    privacy_mode: bool = False

    @property
    def is_online(self) -> bool | None:
        """Return online state using the same status groups as the web client."""

        if self.privacy_mode or self.backend_status is None:
            return None
        if self.backend_status in {"LoggedOff", "Offline", "Offline2", "Arrears"}:
            return False
        if self.backend_status in {"Move", "Stop"}:
            return True
        return None

    @property
    def is_moving(self) -> bool | None:
        """Return whether the tracker reports movement."""

        if self.privacy_mode:
            return None
        if self.backend_status == "Move":
            return True
        if self.backend_status == "Stop":
            return False
        if self.is_stopped is not None:
            return not self.is_stopped
        if self.speed_kmh is not None:
            return self.speed_kmh > 0
        return None

    @property
    def normalized_status(self) -> str | None:
        """Return a stable, human-readable status."""

        if self.privacy_mode:
            return None
        mapping = {
            "Move": "moving",
            "Stop": "stopped",
            "Offline": "offline",
            "Offline2": "offline",
            "LoggedOff": "logged_off",
            "Arrears": "arrears",
        }
        if self.backend_status is None:
            return None
        return mapping.get(self.backend_status, "unknown")

    @classmethod
    def from_raw(
        cls,
        raw: dict[str, Any],
        *,
        backend_device_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> "WinnesDeviceData":
        """Build normalized data from one backend device object."""

        combined: dict[str, Any] = {}
        if metadata:
            combined.update(metadata)
        combined.update(raw)

        model = str(combined["model"]) if combined.get("model") not in (None, "") else None
        raw_name = combined.get("name")
        raw_model_name = combined.get("modelName")

        return cls(
            backend_device_id=backend_device_id,
            name=str(raw_name) if raw_name not in (None, "") else None,
            model=model,
            model_name=(
                str(raw_model_name) if raw_model_name not in (None, "") else None
            ),
            latitude=_as_float(combined.get("latitude")),
            longitude=_as_float(combined.get("longitude")),
            server_time=_as_utc_datetime(combined.get("serverUtcDate")),
            device_time=_as_utc_datetime(combined.get("deviceUtcDate")),
            speed_kmh=_as_float(combined.get("speed")),
            course_degrees=_as_float(combined.get("course")),
            position_source=normalize_position_source(combined.get("dataType")),
            total_distance_km=_as_float(combined.get("distance")),
            is_stopped=_as_bool_from_int(combined.get("isStop")),
            stop_minutes=_as_int(combined.get("stopTimeMinute")),
            offline_minutes=_as_int(combined.get("ofl")),
            backend_status=(
                str(combined["status"]) if combined.get("status") not in (None, "") else None
            ),
            battery_percent=decode_battery_percent(model, combined.get("dataContext")),
        )

    @classmethod
    def private(
        cls,
        backend_device_id: int,
        *,
        name: str | None = None,
        model: str | None = None,
        model_name: str | None = None,
    ) -> "WinnesDeviceData":
        """Return a fail-closed state containing no live telemetry."""

        return cls(
            backend_device_id=backend_device_id,
            name=name,
            model=model,
            model_name=model_name,
            privacy_mode=True,
        )
