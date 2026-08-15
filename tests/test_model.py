"""Tests for the standard-library-only WINNES payload model."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "winnes_gps"
    / "model.py"
)
SPEC = importlib.util.spec_from_file_location("winnes_model", MODEL_PATH)
assert SPEC is not None and SPEC.loader is not None
MODEL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODEL
SPEC.loader.exec_module(MODEL)


class PayloadTests(unittest.TestCase):
    def test_parse_legacy_payload(self) -> None:
        payload = (
            '{devices:[{id:1234,name:"Demo, Tracker: A",model:"152",'
            'modelName:"TK915",latitude:"47.00000",longitude:"19.00000",'
            'speed:"0.00",speed:"12.50",course:"90",dataType:"1",'
            'dataContext:"-74",distance:"123.45",isStop:0,stopTimeMinute:0,'
            'ofl:"0",status:"Move",deviceUtcDate:"2026-08-16 10:00:00",'
            'serverUtcDate:"2026-08-16 10:00:05"}]}'
        )
        devices = MODEL.parse_legacy_devices(payload)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["id"], 1234)
        self.assertEqual(devices[0]["name"], "Demo, Tracker: A")
        self.assertEqual(devices[0]["speed"], "12.50")

    def test_tk915_battery_decode(self) -> None:
        self.assertEqual(MODEL.decode_battery_percent("152", "-74"), 74)
        self.assertIsNone(MODEL.decode_battery_percent("152", "-101"))
        self.assertIsNone(MODEL.decode_battery_percent("9999", "-74"))

    def test_normalization(self) -> None:
        raw = {
            "id": 1234,
            "name": "Demo Tracker",
            "model": "152",
            "modelName": "TK915",
            "latitude": "47.0",
            "longitude": "19.0",
            "speed": "12.5",
            "course": "90",
            "dataType": "1",
            "dataContext": "-74",
            "distance": "123.45",
            "isStop": 0,
            "stopTimeMinute": 0,
            "ofl": "0",
            "status": "Move",
            "deviceUtcDate": "2026-08-16 10:00:00",
            "serverUtcDate": "2026-08-16 10:00:05",
        }
        data = MODEL.WinnesDeviceData.from_raw(raw, backend_device_id=1234)
        self.assertTrue(data.is_online)
        self.assertTrue(data.is_moving)
        self.assertEqual(data.position_source, "GPS")
        self.assertEqual(data.battery_percent, 74)
        self.assertEqual(data.normalized_status, "moving")

    def test_privacy_data_contains_no_telemetry(self) -> None:
        data = MODEL.WinnesDeviceData.private(
            1234, name="Demo Tracker", model="152", model_name="TK915"
        )
        self.assertTrue(data.privacy_mode)
        self.assertIsNone(data.latitude)
        self.assertIsNone(data.longitude)
        self.assertIsNone(data.speed_kmh)
        self.assertIsNone(data.is_online)
        self.assertIsNone(data.is_moving)


if __name__ == "__main__":
    unittest.main()
