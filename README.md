# ZTE H186 DSL Statistics

Copyright (C) 2026 Daniel Ebenhöh. Licensed under the GNU General Public
License v3.0 only; see [LICENSE](LICENSE).

Read DSL line statistics from a ZTE H186 modem without a browser. The client
uses the modem's read-only status endpoint and Python's standard library.

The modem address and administrator password are required local inputs. The
client reads both only from encrypted files in `secrets/`; it has no built-in
address or password fallback.

## Quick Start

Requirements: Python 3.10 or later, `age`, and `age-keygen`.

1. From the project root, create the encrypted modem address:

  ```sh
  ./store-age-secret.sh zte-ipaddress
  ```

  Enter only the modem's IPv4 or IPv6 address when prompted.

2. Create the encrypted administrator password:

  ```sh
  ./store-age-secret.sh zte-admin-password
  ```

3. Fetch the current DSL statistics:

  ```sh
  python3 zte_h186_stats.py
  ```

For machine-readable output, use `python3 zte_h186_stats.py --json`.

The helper encrypts both values into `secrets/`. The client selects the newest
matching `zte-ipaddress-*.age` and `zte-admin-password-*.age` file. The files
are excluded from Git. See [Setup](docs/SETUP.md) before first use and
[Security](docs/SECURITY.md) before publishing or sharing a checkout.

Run the local test suite with:

```sh
python3 -m unittest discover -s tests -v
```

## Project Layout

- `zte_h186_stats.py`: authenticated, read-only DSL statistics client.
- `store-age-secret.sh`: local age encryption helper.
- `secrets/`: per-user encrypted address and password; never commit its contents.
- `docs/PROTOCOL.md`: modem request sequence and returned fields.
- `docs/SETUP.md`: installation and first-run steps.
- `docs/SECURITY.md`: handling identities, secrets, and collected statistics.
- `LICENSE` and `pyproject.toml`: license text and project metadata.