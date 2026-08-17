# Changelog

All notable changes to this project are documented here.

## 0.1.1 - 2026-08-17

Backend compatibility fix based on the current mytkstar.net web request profile.

- Match the official web client's `application/json` content type and same-origin request headers on the primary polling attempt.
- Use a map-page referer shape matching the current mytkstar.net client.
- Retry automatically with the previous minimal request profile when the backend rejects or changes the primary response shape.
- Accept both the observed legacy string payload and a normal JSON `d.devices` payload without executing JavaScript.
- Keep response bodies out of logs and errors so exact location and tracker details are not exposed during setup failures.

## 0.1.0 - 2026-08-16

Initial public build.

- Native Home Assistant GPS `device_tracker`.
- Battery, speed, timestamp, status and diagnostic sensors.
- Online and moving binary sensors.
- Persistent fail-closed Privacy mode switch.
- Zero WINNES HTTP requests while Privacy mode is active.
- UI config flow using backend User ID and Device ID; no tracker password stored.
- Configurable 10-300 second polling interval (30 seconds by default).
- Non-executing parser for the legacy ASP.NET/JavaScript-style response payload.
- Privacy-preserving diagnostics.
- HACS metadata, validation workflow, tests, security guidance and documentation.
