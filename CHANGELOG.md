# Changelog

All notable changes to the ZTE H186 Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-11-13

### Changed
- **License changed from GPL-3.0-only to MIT** — more permissive and the de-facto
  standard in the Home Assistant / HACS ecosystem. Updated `LICENSE`, every SPDX
  header, `pyproject.toml`, `package.json`, the README license badges/sections
  (en/de/fr/es) and the governance docs.
- **Version consistency restored:** `manifest.json`, `package.json` and
  `pyproject.toml` bumped from the stale `1.0.0` to `1.2.1`. These files had never
  been updated past the initial release even though tags advanced to v1.2.0, so HACS
  and Home Assistant reported the integration as `1.0.0`.
- Release-archive references updated from `zte-h186-v1.0.0.zip` to `zte-h186-v1.2.1.zip`.

### Fixed
- Changelog backfilled: the v1.0.1 – v1.2.0 releases were missing from this file.

## [1.2.0] - 2026-10-26

### Changed
- Complete project review: SSRF protection for the companion web server, brand-icon
  proxy support for Home Assistant, manifest/CI adjustments, and multilingual
  documentation and navigation.

## [1.1.1] - 2026-10-25

### Added
- Integration brand icon.

## [1.1.0] - 2026-10-25

### Changed
- Full internationalization (i18n): migrated all user-facing text to the translation
  framework; added English, German, French and Spanish localization files.

## [1.0.1] - 2026-10-25

### Fixed
- aiohttp IP-address cookie handling; config-flow inputs are now preserved when
  validation fails.

## [1.0.0] - 2026-10-25

### Added
- Complete HACS integration for ZTE H186 DSL modems.
- Config Flow (UI-based setup), dynamic Reconfigure Flow (change modem IP/password
  without losing entities or history), and Options Flow (polling interval 15–600 s).
- Full asynchronous API client using `aiohttp` and `DataUpdateCoordinator`.
- 27 sensor entities covering sync speeds, attainable rates, SNR margins, attenuation,
  transmit power, line framing, uptime, and CRC/FEC error counters.
- Binary sensors for DSL physical connectivity and low-SNR noise warning.
- Action button to trigger an immediate modem poll.
- Diagnostics support with automatic password redaction.
- Bilingual localization (English & German) and modern ConfigEntry runtime-data architecture.
