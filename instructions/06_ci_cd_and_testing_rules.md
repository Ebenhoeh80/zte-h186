# 06 - CI/CD, Quality Scales & Testing Rules

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](#english) | [Deutsch](#deutsch)

---

## English

### 1. Automated Validation Pipeline
The repository utilizes GitHub Actions to validate every commit and pull request:

```text
.github/workflows/
  ├── validate.yml        # Hassfest, HACS action, Python unit tests
```

### 2. Hassfest Validation
- **Engine**: `ghcr.io/home-assistant/hassfest`
- **Rules Verified**:
  - `manifest.json` ordering: `domain`, `name`, then alphabetical.
  - Manifest schema validity (No forbidden keys like `categories`).
  - Translations completeness: `strings.json` and matching translation files.
  - Codeowners format.
- **Local Testing**:
  ```bash
  docker run --rm -v $(pwd):/github/workspace ghcr.io/home-assistant/hassfest
  ```

### 3. HACS Action Validation
- **Engine**: `hacs/action`
- **Requirements**:
  - GitHub repository must have valid topics (e.g. `home-assistant`, `hacs`, `custom-integration`).
  - GitHub repository must have a public description.
  - Integration files must reside in `custom_components/zte_h186/`.
  - `hacs.json` present in repository root.

### 4. Unit Testing Suite
- **Framework**: Python standard library `unittest`.
- **Command**:
  ```bash
  python3 -m unittest discover -s tests -v
  ```
- **Requirements**:
  - All tests must run completely offline without actual network sockets or external dependencies.
  - Uses synthetic HTML/XML fixtures and mocks for authentication, session cookies, and DSL XML responses.
  - 100% test pass rate required prior to release or push.

### 5. Release Packaging
- Execute `python3 create_release_zip.py` to generate `zte-h186-v<VERSION>.zip` containing `custom_components/zte_h186/` and release metadata.

---

## Deutsch

### 1. Validierungs-Pipeline
Automatisierte CI/CD-Workflows in `.github/workflows/validate.yml` prüfen jeden Commit:
1. **Hassfest**: Manifest-Reihenfolge (`domain`, `name`, alphabetisch), keine unzulässigen Schlüssel (z. B. kein `categories`), Vollständigkeit von `strings.json`.
2. **HACS**: Repository-Topics, Beschreibung, `hacs.json`.
3. **Unit Tests**: Vollständig offline via `python3 -m unittest discover -s tests -v`.
4. **Release-Paket**: Erstellung des Distributionsarchivs über `python3 create_release_zip.py`.
