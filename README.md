# WINNES GPS for Home Assistant

A lightweight Home Assistant custom integration for WINNES / TKSTAR GPS trackers that use the `mytkstar.net` web platform.

The integration creates a native `device_tracker` plus useful telemetry entities without running Traccar, an MQTT bridge, a database, or another Home Assistant add-on.

> [!IMPORTANT]
> This project is unofficial and is not affiliated with WINNES, TKSTAR, or mytkstar.net. It uses the web platform's existing polling interface, which is undocumented and can change without notice.

## Privacy by design

This integration was deliberately designed not to store your tracker login password.

Setup uses two internal numeric backend IDs that your own logged-in browser already sends in the `GetDevicesByUserID` request. The integration does not implement CAPTCHA bypass, account enumeration, device discovery, or broad ID scanning.

It also provides a persistent **Privacy mode** switch. While Privacy mode is on:

- no WINNES/mytkstar HTTP requests are made by this integration;
- latitude and longitude are removed from the live Home Assistant entity state;
- telemetry sensors become unavailable rather than continuing to expose stale live data;
- the setting survives a Home Assistant restart;
- turning Privacy mode off immediately requests fresh data again.

Privacy mode affects only Home Assistant. It does **not** stop the physical tracker from sending data to the WINNES cloud, and it does not delete location history that Home Assistant Recorder already stored.

Diagnostics are intentionally redacted: exact backend IDs, coordinates, tracker name, speed, distance, and timestamps are not exported.

## Entities

A configured tracker exposes:

| Entity | Purpose |
| --- | --- |
| `device_tracker.*` | Native GPS location for the HA map, zones, proximity and automations |
| `sensor.*_battery` | Tracker battery percentage when the model encoding is known |
| `sensor.*_speed` | Speed in km/h |
| `sensor.*_last_position` | Timestamp of the GPS fix |
| `binary_sensor.*_online` | Online/offline status |
| `binary_sensor.*_moving` | Moving/stopped status |
| `switch.*_privacy_mode` | Persistent fail-closed privacy control |

Additional diagnostic entities expose position source (GPS/LBS/Wi-Fi), backend status, total distance, course, stop duration, offline duration and server update time when those fields are available.

Battery decoding is currently verified against the TK915 backend model family used by the original implementation. Unknown model encodings are left unavailable rather than guessed.

## Installation with HACS

1. Open **HACS → Integrations**.
2. Open the three-dot menu → **Custom repositories**.
3. Add `https://github.com/ArrowSK/ha-winnes-gps` as category **Integration**.
4. Install **WINNES GPS**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration → WINNES GPS**.

Manual installation is also possible: copy `custom_components/winnes_gps` into your Home Assistant `custom_components` directory, restart Home Assistant, then add the integration from the UI.

## Finding the two setup IDs

Do this only for a tracker/account that you own or are authorized to administer.

1. Log in normally at `mytkstar.net` in a desktop browser.
2. Open Developer Tools → **Network**.
3. Filter for `GetDevicesByUserID`.
4. Select one of those requests and open its **Payload** / request-body view.
5. Note only the numeric values named `UserID` and `DeviceID`.
6. Enter those two values in the WINNES GPS Home Assistant setup form.

These are **internal backend IDs**. `DeviceID` in this request is not necessarily the IMEI/tracker number printed on the hardware.

Do not upload or publish a HAR capture. HAR files can contain exact location, tracker identifiers, registration details, passwords or other private data depending on what was captured. This repository intentionally ignores `*.har` and packet-capture files.

## Polling

The default polling interval is **30 seconds**. It can be changed from **10 to 300 seconds** in the integration options.

The official web interface observed during development polls the same device endpoint more frequently. The Home Assistant default is intentionally more conservative.

When the backend is unreachable or returns an unexpected payload, entities become unavailable through Home Assistant's normal coordinator behavior. The integration does not fall back to cached coordinates as if they were current.

## Avoid storing location history in Home Assistant

If you want live zones/automations but do not want Home Assistant Recorder to retain the tracker's location history, exclude the generated tracker entity in `configuration.yaml`:

```yaml
recorder:
  exclude:
    entities:
      - device_tracker.your_winnes_tracker
```

Use your actual entity ID, then restart Home Assistant. This is separate from Privacy mode: Recorder exclusion controls local history; Privacy mode controls whether this integration polls WINNES at all.

## How it works

The current mytkstar web client polls an ASP.NET endpoint named `GetDevicesByUserID`. Its response contains an outer JSON envelope and a legacy JavaScript-style object literal inside the `d` field. This integration:

- sends only the exact `UserID` and `DeviceID` configured by the user;
- parses the legacy payload with a non-executing parser (no `eval`, no JavaScript engine);
- retains only the metadata needed by Home Assistant;
- does not persist tracker serial number or vehicle registration returned by the first web response;
- normalizes coordinates, speed, status, position source, timestamps and supported battery formats;
- uses Home Assistant's `DataUpdateCoordinator` for polling and availability handling.

## Known limitations

- The backend API is undocumented and can change.
- Setup currently requires the two internal IDs from your own browser session. The integration intentionally does not automate the IMEI/password/CAPTCHA login flow.
- If WINNES starts requiring a new authentication mechanism on the polling endpoint, the integration will fail closed and report unavailable until support is added.
- Battery formats vary by tracker model. Unknown formats are not guessed.
- This integration is read-only. It does not send SMS commands, remote tracker commands, geofence changes, sleep commands, or other control operations.

## Security and responsible use

Use this integration only with devices you own or are explicitly authorized to track. Do not probe, enumerate or test other users' backend IDs.

Never attach HAR files, passwords, exact coordinates, tracker serials, vehicle registrations or live backend IDs to a public GitHub issue. See [SECURITY.md](SECURITY.md) before reporting a security-sensitive problem.

## Development

Local structural checks do not require a full Home Assistant development environment:

```bash
python scripts/validate.py
python -m unittest discover -s tests
python -m compileall -q custom_components scripts tests
```

GitHub Actions also runs HACS validation and Home Assistant `hassfest`.

## License

MIT. See [LICENSE](LICENSE).
