"""Constants for the WINNES GPS integration."""

from homeassistant.const import Platform

DOMAIN = "winnes_gps"
NAME = "WINNES GPS"

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]

CONF_USER_ID = "user_id"
CONF_DEVICE_ID = "device_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_PRIVACY_MODE = "privacy_mode"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 300

BASE_URL = "https://www.mytkstar.net"
DEVICE_ENDPOINT = f"{BASE_URL}/Ajax/DevicesAjax.asmx/GetDevicesByUserID"
MONITOR_URL = f"{BASE_URL}/Monitor.aspx"
REQUEST_TIMEOUT = 15

OFFLINE_STATUSES = frozenset({"LoggedOff", "Offline", "Offline2", "Arrears"})
ONLINE_STATUSES = frozenset({"Move", "Stop"})
