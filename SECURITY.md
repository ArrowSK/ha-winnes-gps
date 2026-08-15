# Security policy

Location data is sensitive. Treat WINNES backend IDs, tracker serial numbers, vehicle registration data, account credentials and HAR/network captures as secrets even if the upstream service does not label them that way.

## Reporting a security issue

Do **not** put credentials, HAR files, backend IDs, exact coordinates, tracker serial numbers, vehicle registrations, or reproducible third-party access details in a public issue.

Prefer GitHub's private vulnerability-reporting flow under the repository's **Security** tab when it is available. If private reporting is not enabled, open a public issue containing only a short request for a private contact channel and no sensitive technical details.

## Scope

This integration is intentionally read-only and deliberately does not implement:

- ID enumeration or account/device discovery;
- CAPTCHA bypass;
- credential harvesting;
- remote SMS/control commands;
- geofence modification;
- tracker sleep/shutdown commands.

The integration only polls the exact backend IDs supplied by the Home Assistant administrator.

## Diagnostics

Home Assistant diagnostics from this integration omit exact coordinates, exact timestamps, speed, distance, tracker name and backend IDs. Configuration IDs are redacted.

Even so, review any diagnostic file before sharing it publicly.
