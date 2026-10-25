# Changelog

All notable changes to the ZTE H186 Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-25

### Added
- Complete HACS integration for ZTE H186 DSL Modems.
- Config Flow (UI-based setup via Home Assistant web interface).
- Dynamic Reconfigure Flow to update modem IP or password without losing entities or history.
- Options Flow to configure polling scan interval (15s to 600s).
- Full asynchronous API client using `aiohttp` and `DataUpdateCoordinator`.
- 26 Sensor entities covering sync speeds, attainable rates, SNR margins, attenuation, transmit power, framing, uptime, and CRC/FEC error counters.
- Binary sensor for DSL physical connectivity and low SNR noise warnings.
- Diagnostics support (`async_get_config_entry_diagnostics`) with automatic password redaction.
- Action button to trigger immediate modem polling.
- Full bilingual localization (English & German).
- Modern ConfigEntry Runtime Data architecture.
