# Changelog

All notable changes to the ZTE H186 Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.1] - 2026-11-20

### Changed
- **The entry title shows the serial number in parentheses:** "ZTE H186 (ZTEE09RKCA00542)". An entry with a
  generated title is renamed at the next start; a title you chose stays.

## [1.5.0] - 2026-11-20

### Changed
- **The modem is identified by its serial number, not by its address.** The entry's unique id, its title
  (`ZTE H186 <serial>`), the device and the entities' unique ids now use the serial number that the modem reports
  about itself. Before, the address (older installations) or the id of the config entry identified them. Existing
  entries are migrated at the next start without losing entities, history, areas or names; a title you chose stays.
  See [`docs/IDENTITY.md`](docs/IDENTITY.md).
- **The device shows what the modem reports:** serial number, model, hardware and software version.
- **A different modem at the saved address is not taken over:** setup, reconfigure and re-authentication
  compare the serial number and refuse a modem that is not the one of the entry. A second entry for the same modem
  stops with a clear message instead of creating every device twice.
- **DHCP discovery:** a known modem that got a new address is followed (recognised by its hardware address); a
  new H186 is offered under *Discovered*.

### Fixed
- **The integration logs off from the modem.** The modem allows one admin session at a time, and versions up to
  1.4.1 never logged off, so after a reload, a restart or a setup dialog the next login was refused for some
  minutes and a re-authentication was started that was not needed. The client now logs off when it is closed, after
  a failed setup and before a dialog checks a running entry.

## [1.4.1] - 2026-11-20

### Changed
- **Release zip.** `hacs.json` now uses `zip_release`, and a workflow attaches `zte_h186.zip`
  to every release.

### Fixed
- **No more deprecation warning on Home Assistant 2026.11.** The one-time
  migration of the legacy host-based device looked the device up with
  `device_registry.async_get_device`, which is deprecated (identifiers are no
  longer unique across config entries) and stops working in Home Assistant
  2027.8. It now looks the device up in this config entry only, and falls back to
  the old call on older Home Assistant versions. A test covers the migration.

## [1.4.0] - 2026-11-14

This release takes the integration to the Home Assistant **Gold** quality scale.

### Added
- **Icon translations** (`icons.json`): all entity icons are now defined
  centrally per translation key, including per-state icons for the DSL status.
- **Translated exceptions**: coordinator update failures (auth, connection,
  timeout, protocol) now raise localized messages via `translation_key` in all
  four languages.
- **DSL status is now an enum sensor**: the raw modem value is normalized to a
  fixed, localized option set (`connected`, `disconnected`, `initializing`,
  `idle`, `no_signal`, `disabled`), with a safe fallback so the state is always
  valid. The raw value remains available in Diagnostics.
- `quality_scale.yaml` documenting the status of every quality-scale rule.
- Expanded documentation: supported devices, supported functions, data-update
  behavior, use-case automation examples, known limitations, troubleshooting,
  and removal instructions.

### Changed
- Manifest quality scale raised from **bronze** to **gold**.
- The refresh button no longer uses the misleading `update` device class; it now
  carries a proper refresh icon via `icons.json`.
- README entity IDs corrected (the legacy `<ip>` segment is no longer part of the
  entity IDs after the 1.3.0 registry migration).

## [1.3.0] - 2026-11-14

This release repairs a broken login, hardens the companion web server, and
modernizes the integration toward the Home Assistant Silver quality scale.

### ⚠️ Breaking changes
- **Minimum Home Assistant version is now 2025.8** (`OptionsFlowWithReload`,
  `AddConfigEntryEntitiesCallback`, entity-registry migration).
- **Entity unique IDs and the device identity are now based on the config entry,
  not the modem IP.** Existing entities and the device are migrated automatically
  on upgrade, so history is preserved; the device is now named "ZTE H186" without
  the IP suffix.
- **Missing line metrics report "unknown" instead of 0.** While the line is
  down/training, SNR, attenuation, power, profile and modulation are now unknown
  rather than a misleading `0.0` / `"None"`.
- Removed the raw-XML attribute dump from the DSL status sensor (recorder bloat);
  the full raw values remain available via Diagnostics.
- `showtime` is no longer a `TOTAL_INCREASING` statistic (uptime resets on resync).

### Fixed
- **Login was completely broken:** the client sent a stray `_sessionTOKEN` field,
  so the modem issued an unauthorized session and every poll failed with
  `SessionTimeout` / HTTP 404. The login now matches the modem's own web form.

### Security (companion dashboard `server.ts`)
- Fixed path traversal in the brand-image proxy (arbitrary LAN file read).
- `ZTE_MODEM_PASSWORD` is only used for the configured host (closes a password-hash
  oracle); removed open CORS; the server now binds to `127.0.0.1` by default
  (`HOST` env to override); every upstream request uses `redirect: 'manual'` and an
  8-second timeout (SSRF / hang hardening).

### Added
- Re-authentication flow: wrong or changed credentials trigger a Home Assistant
  reauth prompt instead of silent retries.
- Diagnostics now include the full normalized data, raw XML values and the last
  exception (username/host/password redacted).
- `data_description` help text for the setup fields (en/de/fr/es).

### Changed / internal
- New `ZteH186Entity` base class; `PARALLEL_UPDATES`; power uses the dBm unit
  constant; `configuration_url` derives from the API client (IPv6-safe).
- Tooling: Ruff (lint + format), mypy and pytest config; `requires-python` 3.13.
- CI overhauled: Python 3.13, Ruff jobs, a Node job (tsc / Vitest / Vite build),
  `permissions` and `concurrency`.
- Host validation extracted to `src/server/validateHost.ts` with 29 Vitest SSRF
  cases (replacing a dev-server-only test that silently skipped in CI).
- Removed the dead `register_static_path` brand hack (Core serves `brand/` since 2026.3).

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
