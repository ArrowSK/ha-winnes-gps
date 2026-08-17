# Changelog

All notable changes to this project are documented here.

## 0.1.6 - 2026-08-17

HACS 2.0.5 installation-path fix.

- Return to HACS's standard tagged repository-archive installation path instead of `zip_release` mode. HACS 2.0.5 explicitly strips the internal `tags/` prefix before downloading `archive/refs/tags/<version>.zip`, which is the path this release now validates end to end.
- Keep stable GitHub releases as the version source and keep the default branch hidden from the version selector.
- After publishing a new release, make one harmless metadata commit on `main` so a HACS instance that cached the repository before the release existed cannot keep receiving an unchanged repository ETag and remain stuck in Commit mode.
- Update the post-release smoke test to verify HACS release discovery, tagged metadata, and the exact tagged repository archive layout used by HACS 2.0.5.
- No Home Assistant runtime behavior changed in this release.

## 0.1.5 - 2026-08-17

HACS end-to-end release proof.

- Validate the same GitHub release-list behavior HACS 2.0.5 uses to decide between Version and Commit mode.
- Read tagged HACS metadata through GitHub's authenticated Contents API, matching HACS's normal latest-release metadata path and avoiding unrelated raw-content throttling in the smoke test.
- Download the actual published `winnes_gps.zip` release asset with redirects and bounded retries, then verify its required files and manifest version.
- Keep the hardened validation and release-publication retry logic introduced in 0.1.4.
- No Home Assistant runtime behavior changed in this release.

## 0.1.4 - 2026-08-17

HACS release verification hardening.

- Add an end-to-end post-release smoke test that uses the same GitHub release-list behavior HACS 2.0.5 relies on.
- Retry transient GitHub API failures during HACS validation, release discovery, release creation, and release verification instead of silently falling back to commit mode or publishing an incomplete release.
- Run the HACS validator directly from its official container image so GitHub codeload rate limiting cannot prevent the validator itself from starting.
- Verify that HACS selects the newest stable release, that the tagged `hacs.json` points to `winnes_gps.zip`, and that the ZIP contains a matching integration manifest.
- No Home Assistant runtime behavior changed in this release.

## 0.1.3 - 2026-08-17

HACS release-selection fix.

- Hide the default branch from the HACS version selector so HACS does not try to install an abbreviated commit reference instead of a published release.
- Keep HACS installs on immutable GitHub releases with the explicit `winnes_gps.zip` asset.
- Stop rewriting assets on an already-published version; a manifest version now maps to one fixed release.

## 0.1.2 - 2026-08-17

HACS distribution reliability fix.

- Publish an explicit `winnes_gps.zip` asset with every GitHub release.
- Configure HACS `zip_release` mode so installs and upgrades use that release asset instead of relying on repository archive download behavior.
- Refresh the release asset automatically when a release already exists.

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
