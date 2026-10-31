# 02 - Home Assistant Integration Rules & Hassfest Compliance

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](#english) | [Deutsch](#deutsch)

---

## English

### 1. `manifest.json` Rules & Hassfest Validation
Home Assistant's strict linter (`hassfest`) validates the integration manifest against official core schemas. The following rules are mandatory:

1. **Key Sorting**:
   - The first key MUST be `"domain"`.
   - The second key MUST be `"name"`.
   - All subsequent keys MUST be sorted in strict **alphabetical order**:
     `codeowners`, `config_flow`, `documentation`, `integration_type`, `iot_class`, `issue_tracker`, `requirements`, `version`.
2. **Unsupported Keys Prohibited**:
   - **CRITICAL**: Do NOT include `"categories"` in `custom_components/zte_h186/manifest.json`. The `categories` key is rejected by Hassfest for custom integrations and causes immediate build failure:
     ```text
     [MANIFEST] Invalid manifest: not a valid option at 'categories'. Got ['network']
     ```
   - HACS metadata belongs in `hacs.json` in the repository root, not in `manifest.json`.
3. **Mandatory Manifest Keys**:
   - `"domain"`: `"zte_h186"`
   - `"name"`: `"ZTE H186 DSL Modem"`
   - `"codeowners"`: `["@Ebenhoeh80"]`
   - `"config_flow"`: `true`
   - `"integration_type"`: `"device"`
   - `"iot_class"`: `"local_polling"`

### 2. Integration Architecture
1. **Runtime Data Storage**:
   - Must use `entry.runtime_data = coordinator` as defined in modern Home Assistant architecture (2024+).
   - Deprecated `hass.data[DOMAIN][entry_id]` patterns must not be used.
2. **DataUpdateCoordinator**:
   - Manages asynchronous polling via `aiohttp`.
   - Caches active session tokens and cookies. Recovers transparently from session invalidation by re-authenticating.
3. **Configuration & Option Flows**:
   - `config_flow.py` must support:
     - Initial setup (`async_step_user`).
     - Reconfiguration (`async_step_reconfigure`) allowing update of host or password without losing entity registry IDs.
     - Options flow (`async_step_init`) with adjustable update interval (15 to 600 seconds).
4. **Diagnostics**:
   - Implement `diagnostics.py` returning sanitized configuration entry and coordinator state.
   - Credentials (passwords, usernames, session IDs) must be automatically redacted.
5. **Entity Design**:
   - 27 telemetric sensors with exact units, state classes (`measurement`), and sensor device classes.
   - 2 binary sensors (`dsl_link`, `line_noise_warning`).
   - 1 button (`refresh_stats`) triggering immediate coordinator refresh.

---

## Deutsch

### 1. `manifest.json`-Regeln & Hassfest-Konformität
Der offizielle Home-Assistant-Linter (`hassfest`) prüft das Manifest streng nach Schema:

1. **Sortierung der Schlüssel**:
   - Der erste Schlüssel MUSS `"domain"` sein.
   - Der zweite Schlüssel MUSS `"name"` sein.
   - Alle weiteren Schlüssel MÜSSEN in streng **alphabetischer Reihenfolge** vorliegen:
     `codeowners`, `config_flow`, `documentation`, `integration_type`, `iot_class`, `issue_tracker`, `requirements`, `version`.
2. **Keine unzulässigen Schlüssel**:
   - **WICHTIG**: Der Schlüssel `"categories"` darf NICHT in `manifest.json` stehen! Hassfest bricht mit Fehler ab, wenn `"categories"` in Custom Integrations vorhanden ist.
   - HACS-Metadaten gehören in `hacs.json` im Repository-Root, nicht in `manifest.json`.
3. **Erforderliche Schlüssel**:
   - Siehe englischen Abschnitt oben für Pflichtschlüssel.

### 2. Integrations-Architektur
1. **Runtime Data**: Verwendung von `entry.runtime_data = coordinator` (HA-Standard seit 2024).
2. **DataUpdateCoordinator**: Verwaltet asynchrone HTTP-Abfragen via `aiohttp`, hält die Sitzung aktiv und behandelt Session-Timeouts automatisch.
3. **Flows**: UI Config Flow, Reconfigure Flow (IP-/Passwortwechsel ohne Entitätsverlust) und Options Flow (Scan-Intervall 15–600 Sekunden).
4. **Diagnose**: `diagnostics.py` zur Bereitstellung bereinigter Diagnose-Dumps (Passwörter und Tokens maskiert).
5. **Entitäten**: 27 Sensoren, 2 Binärsensoren und 1 Aktualisierungsbutton.
