# 03 - Mandatory 4-Language Policy (i18n & Documentation)

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](#english) | [Deutsch](#deutsch)

---

## English

### 1. Mandatory 4-Language Principle
The project establishes a strict policy: **all public documentation, user guides, setup instructions, and user interface elements must be provided and maintained in the four official project languages**:

| Code | Language | Role / Scope |
|---|---|---|
| `en` | **English** | Canonical source language for code, strings, and default documentation |
| `de` | **German (Deutsch)** | Complete technical localization for documentation and UI |
| `fr` | **French (Français)** | Complete technical localization for documentation and UI |
| `es` | **Spanish (Español)** | Complete technical localization for documentation and UI |

### 2. Implementation in Custom Component UI
1. **Source Strings**: All user-visible strings must be defined in `custom_components/zte_h186/strings.json` (English).
2. **Translation Files**:
   - `custom_components/zte_h186/translations/en.json`
   - `custom_components/zte_h186/translations/de.json`
   - `custom_components/zte_h186/translations/fr.json`
   - `custom_components/zte_h186/translations/es.json`
3. All four translation files must remain in exact 1:1 structural parity with `strings.json`. No untranslated English fallbacks or missing keys in `de`, `fr`, or `es`.

### 3. Implementation in Documentation (`/docs`)
1. **Documentation Parity Rule**:
   Every topic documented under `/docs/` must exist in all 4 languages:
   - `HomeAssistant.md`: Local DSL telemetry integration, cabling, setup, and sensors.
   - `SETUP.md`: Credential methods (JSON, CLI/Env, Age encryption, HA UI), requirements, and troubleshooting.
   - `PROTOCOL.md`: Web interface reverse-engineered handshake protocol (5-step login and data endpoint).
   - `SECURITY.md`: Secret handling, Age identity security, runtime memory hygiene, and public release audit.
2. **Directory Structure**:
   - Root index: `docs/README.md` providing links in all 4 languages.
   - Language-specific subdirectories:
     - `/docs/en/` (English)
     - `/docs/de/` (German)
     - `/docs/fr/` (French)
     - `/docs/es/` (Spanish)
   - Top-level files in `/docs/` (`HomeAssistant.md`, `SETUP.md`, `PROTOCOL.md`, `SECURITY.md`) maintain header language switches to navigate seamlessly to any of the 4 translations, ensuring backward compatibility for existing external links and anchors.

### 4. Root Documentation
- `README.md` (Canonical English)
- `README.de.md` (Complete German version)
- `README.fr.md` (Complete French version)
- `README.es.md` (Complete Spanish version)
- Top banner with language navigation: `[English](README.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md)`.

---

## Deutsch

### 1. Verbindliche 4-Sprachen-Vorgabe
Das Projekt schreibt verbindlich vor: **Sämtliche öffentliche Dokumentationen, Installationsanleitungen, Verkabelungshilfen und Benutzeroberflächen müssen lückenlos in den vier offiziellen Projektsprachen bereitgestellt werden**:

1. **Englisch (`en`)**: Kanonische Quellsprache.
2. **Deutsch (`de`)**: Vollständige Lokalisierung.
3. **Französisch (`fr`)**: Vollständige Lokalisierung.
4. **Spanisch (`es`)**: Vollständige Lokalisierung.

### 2. Umsetzung im Home-Assistant-Code
- Alle Texte in `strings.json` müssen synchron in den vier Übersetzungsdateien unter `custom_components/zte_h186/translations/{en,de,fr,es}.json` gepflegt sein.

### 3. Umsetzung unter `/docs`
- Jedes Dokument (`HomeAssistant.md`, `SETUP.md`, `PROTOCOL.md`, `SECURITY.md`) muss in allen 4 Sprachen unter `/docs/{en,de,fr,es}/` vorliegen.
- Unter `/docs` bietet ein Sprachauswahl-Header die direkte Umschaltung.
- Keine englischen oder deutschen Alleingänge: Teildokumentationen in nur einer Sprache sind unzulässig.

### 4. Root-READMEs
- Neben dem englischen `README.md` existieren vollwertige Übersetzungen `README.de.md`, `README.fr.md` und `README.es.md`.
