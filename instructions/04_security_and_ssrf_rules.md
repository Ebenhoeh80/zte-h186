# 04 - Security, SSRF Defense & Credential Rules

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](#english) | [Deutsch](#deutsch)

---

## English

### 1. Server-Side Request Forgery (SSRF) Defense
Because the integration performs HTTP requests based on user-provided host configurations, strict SSRF defenses are implemented in `custom_components/zte_h186/api.py` and `zte_h186_stats.py`:

1. **Permitted Target Addresses**:
   - Only **RFC 1918 Private IPv4 Addresses**:
     - `10.0.0.0/8`
     - `172.16.0.0/12`
     - `192.168.0.0/16`
   - Local loopback: `127.0.0.1`, `::1` (for test environments).
2. **Strictly Prohibited & Rejected Addresses**:
   - Cloud instance metadata services (e.g., `169.254.169.254` or `metadata.google.internal`).
   - Link-local addresses (`169.254.0.0/16`, `fe80::/10`).
   - Multicast ranges (`224.0.0.0/4`).
   - Broadcast and 0.0.0.0.
   - Public WAN IP addresses or arbitrary Internet endpoints.
3. **Resolution & Hostname Validation**:
   - Hostnames are resolved to IP before validation; DNS rebinding attacks or resolutions pointing to disallowed ranges raise `ZteH186ConnectionError("Host address not allowed: ...")`.

### 2. Credential Security & Encryption at Rest
1. **Age Secrets for Standalone/CLI Execution**:
   - Modem IP and administrator password must be encrypted using `age` via `./store-age-secret.sh <purpose>`.
   - Files are written to `secrets/zte-*.age`.
   - `secrets/` and `*.age` are strictly git-ignored.
2. **Home Assistant UI Configuration**:
   - Passwords must be entered via `vol.Required(CONF_PASSWORD): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD))`.
   - Never expose plaintext passwords in configuration files or logs.
3. **Diagnostics Sanitization**:
   - `diagnostics.py` uses `async_redact_data` with `TO_REDACT = {CONF_PASSWORD, CONF_USERNAME, "session_token", "sid", "cookies"}`.

### 3. ZTE Modem Protocol Hygiene
1. **Hex-Decoded Session Token**: The modem delivers `_sessionTmpToken` embedded with hex-escapes (e.g. `\x2f`). These must be correctly decoded prior to session initialization.
2. **SHA-256 Challenge Hashing**: The modem login computes `SHA-256(password + challenge_token)` rather than submitting passwords in plaintext.
3. **Session Priming**: After successful login and SID cookie generation, the client must load `getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp` to establish expected internal state before reading `internet_dsl_interface_lua.lua`.
4. **Session Reuse**: To prevent exhausting modem memory or concurrent login limits, active sessions must be cached and reused across poll cycles.

---

## Deutsch

### 1. Schutz vor Server-Side Request Forgery (SSRF)
Da die Integration HTTP-Anfragen an ein vom Nutzer konfiguriertes Ziel sendet, greift eine strikte SSRF-Schutzlogik:

1. **Erlaubte Zieladressen**:
   - Ausschließlich private IPv4-Bereiche nach RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) sowie lokaler Loopback (`127.0.0.1`, `::1`).
2. **Gesperrte Adressen**:
   - Cloud-Metadatendienste (`169.254.169.254`), Link-Local (`169.254.0.0/16`), Multicast, Broadcast und öffentliche Internetadressen.
3. **DNS-Prüfung**: Hostnamen werden vor dem Aufruf aufgelöst und die resultierende IP gegen die Sperrliste geprüft.

### 2. Schutz von Zugangsdaten & Verschlüsselung
- Für CLI-Skripte: `age`-Verschlüsselung via `store-age-secret.sh`. Das Verzeichnis `secrets/` ist git-ignoriert.
- Im Home Assistant: Maskierte Passworteingabe im UI, keine Passwörter in Logs, automatische Bereinigung in `diagnostics.py`.

### 3. Protokoll-Regeln
- Korrekte Hex-Escape-Dekodierung von `_sessionTmpToken`.
- SHA-256-Hash des Passworts mit Challenge-Token.
- Priming der Sitzung über `getpage.lua`, bevor Daten aus `internet_dsl_interface_lua.lua` abgefragt werden.
- Sitzungs-Caching zur Schonung der Modem-Ressourcen.
