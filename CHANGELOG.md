# Changelog

All notable changes to this project are documented here.

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
