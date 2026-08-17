"""Small repository checks that do not require Home Assistant to be installed."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "winnes_gps"
COMPONENT = ROOT / "custom_components" / DOMAIN

REQUIRED = (
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "hacs.json",
    ROOT / "SECURITY.md",
    COMPONENT / "__init__.py",
    COMPONENT / "api.py",
    COMPONENT / "binary_sensor.py",
    COMPONENT / "config_flow.py",
    COMPONENT / "const.py",
    COMPONENT / "coordinator.py",
    COMPONENT / "device_tracker.py",
    COMPONENT / "diagnostics.py",
    COMPONENT / "entity.py",
    COMPONENT / "manifest.json",
    COMPONENT / "model.py",
    COMPONENT / "sensor.py",
    COMPONENT / "strings.json",
    COMPONENT / "switch.py",
    COMPONENT / "translations" / "en.json",
)

FORBIDDEN_SUFFIXES = {".har", ".pcap", ".pcapng"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")

    captured = [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if captured:
        fail("captured network traffic must never be committed")

    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("domain") != DOMAIN:
        fail("manifest domain mismatch")
    if manifest.get("config_flow") is not True:
        fail("config_flow must be enabled")
    if manifest.get("iot_class") != "cloud_polling":
        fail("iot_class must remain cloud_polling")
    if not manifest.get("version"):
        fail("custom integration manifest must contain a version")

    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    if hacs.get("name") != "WINNES GPS":
        fail("unexpected HACS name")
    if hacs.get("zip_release") is True:
        fail("HACS 2.0.5 distribution must use the standard tagged repository archive")
    if "filename" in hacs:
        fail("standard HACS archive distribution must not force a release filename")
    if hacs.get("hide_default_branch") is not True:
        fail("HACS default branch must stay hidden; installs must use releases")

    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads(
        (COMPONENT / "translations" / "en.json").read_text(encoding="utf-8")
    )
    if strings != english:
        fail("translations/en.json must match strings.json for the initial release")

    api_text = (COMPONENT / "api.py").read_text(encoding="utf-8")
    if "eval(" in api_text or "exec(" in api_text:
        fail("API parser must never execute upstream payloads")

    coordinator_text = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    privacy_branch = "if self.privacy_mode:"
    if privacy_branch not in coordinator_text or "return self.api.private_data()" not in coordinator_text:
        fail("privacy mode must short-circuit before network polling")

    print("Repository validation passed")


if __name__ == "__main__":
    main()
