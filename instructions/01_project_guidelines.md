# 01 - Project Guidelines & Governance

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](#english) | [Deutsch](#deutsch)

---

## English

### 1. Project Philosophy & Core Directives
1. **Local-Only & Cloud-Free**: Telemetry retrieval communicates directly with the local ZTE H186 modem web interface. No cloud services, external APIs, telemetry beacons, tracking, or telemetry logs are permitted.
2. **Read-Only Telemetry**: The integration reads DSL link statistics (`Internet_AdminInternetStatus_DSL_t.lp` and `common_page/internet_dsl_interface_lua.lua`). It MUST NEVER modify DSL settings, modem routing, WAN modes, firewall settings, or credentials on the device.
3. **No Hardcoded Credentials or Addresses**: Production IPs, hostnames, and passwords must never be committed to Git. Always use neutral placeholders (e.g. `<MODEM-LAN-IP>`, `<MODEM-PASSWORD>`).
4. **SPDX & Licensing**: All source files and major documentation files must retain:
   ```text
   # Copyright (C) 2026 Daniel Ebenhöh
   # SPDX-License-Identifier: GPL-3.0-only
   ```

### 2. Code Quality & Standards
- **Python**: Python 3.10+ compatible, strictly typed annotations (`typing`), non-blocking asynchronous execution in Home Assistant (`asyncio`, `aiohttp`).
- **Synchronous vs Asynchronous**:
  - The standalone script `zte_h186_stats.py` uses the Python standard library (`urllib.request`) and optional `pyyaml`.
  - The Home Assistant custom component (`custom_components/zte_h186/`) uses `aiohttp` exclusively. Never execute blocking I/O on the HA event loop.
- **Git Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat: ...`, `fix: ...`, `docs: ...`, `chore: ...`, `refactor: ...`, `test: ...`

---

## Deutsch

### 1. Projektphilosophie & Kernvorgaben
1. **Rein lokal und cloudfrei**: Das Auslesen der Leitungsstatistiken erfolgt ausschließlich über die lokale Webschnittstelle des ZTE H186. Es dürfen keinerlei Cloud-Dienste, externe APIs, Telemetrie-Tracker oder externe Logs eingebunden werden.
2. **Ausschließlich lesender Zugriff**: Die Integration liest Telemetrie (`Internet_AdminInternetStatus_DSL_t.lp` und `common_page/internet_dsl_interface_lua.lua`). Sie darf NIEMALS DSL-Konfigurationen, Routing, WAN-Modi oder Passwörter auf dem Modem verändern.
3. **Keine echten Zugangsdaten im Repository**: Reale IP-Adressen, Hostnamen und Passwörter dürfen niemals in Git abgelegt werden. Es sind neutrale Platzhalter wie `<MODEM-LAN-IP>` und `<MODEM-PASSWORT>` zu verwenden.
4. **SPDX- und Urheberrechtskennzeichnung**: Alle Quellcodedateien und Dokumentationen müssen den Copyright- und SPDX-Hinweis enthalten.

### 2. Codequalität & Richtlinien
- **Python**: Kompatibel mit Python 3.10+, Typannotationen (`typing`), asynchrone Ausführung in Home Assistant (`asyncio`, `aiohttp`).
- **Asynchrone Sauberkeit**: Keine blockierenden Aufrufe im Home-Assistant-Event-Loop.
- **Git-Commits**: Konventionelle Commits (`feat:`, `fix:`, `docs:`, etc.).
