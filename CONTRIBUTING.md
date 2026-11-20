# Contributing to ZTE H186 Home Assistant Integration

Thank you for your interest in contributing to the **ZTE H186 Home Assistant Integration**! We welcome bug reports, feature requests, translation contributions, and code improvements.

## Code of Conduct

Please be respectful and considerate in all interactions with community members, maintainers, and users.

## How to Contribute

### 1. Reporting Bugs
- Search existing issues before creating a new report to avoid duplicates.
- Use the **Bug Report** template.
- Include diagnostics data (downloaded from *Settings > Devices & Services > ZTE H186 > Download Diagnostics*). Sensitive data like passwords are automatically redacted.
- Provide Home Assistant Core version, router firmware version, and relevant logs.

### 2. Suggesting Features
- Open a **Feature Request** issue describing the use case and expected benefit.
- Check if your router firmware supports the suggested metric.

### 3. Translations (i18n)
We actively support and maintain translations in:
- **English (`en`)** (Canonical source language)
- **German (`de`)**
- **French (`fr`)**
- **Spanish (`es`)**

To add or update translations:
1. Update `custom_components/zte_h186/strings.json` with any new keys.
2. Update the corresponding `custom_components/zte_h186/translations/<lang>.json` files.
3. Submit a Pull Request.

### 4. Development & Pull Requests
- Follow the Home Assistant [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/).
- Adhere to `asyncio` best practices: never perform synchronous I/O or sleep in the event loop.
- Use typed annotations (`mypy` / `typing`).
- Ensure unit tests pass:
  ```bash
  python3 -m unittest discover -s tests -v
  ```
- Keep commits concise and meaningful following [Conventional Commits](https://www.conventionalcommits.org/).

## AI-assisted contributions

AI assistants are fine to use, with these rules:

- **Say so** in the pull request or issue (for example "prepared with an AI assistant"), so reviewers know to look closely.
- **You are responsible** for the contribution. Read, understand and test everything you submit; do not send unreviewed AI output.
- **Test on real hardware** where the change touches a device. Do not claim a test you did not run.
- **No secrets** in prompts, logs or examples (passwords, tokens, addresses, serial numbers, unlock commands).

The maintainer also works with AI tools. Every change is reviewed and tested by a human before it is released, and pull requests and issues created that way carry a note.
