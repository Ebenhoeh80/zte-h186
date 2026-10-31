# Setup and Configuration

[English](en/Setup.md) | [Deutsch](de/Setup.md) | [Français](fr/Setup.md) | [Español](es/Setup.md)

The ZTE H186 project provides multiple flexible and secure ways to supply connection credentials, depending on your deployment environment (CLI script, Home Assistant Custom Component, or Docker/daemon execution).

## Credential Methods

The client supports four configuration methods in order of priority:

### 1. JSON Credentials File (Recommended for Automation)
Supply a protected local JSON file via `--credentials`:
```sh
python3 zte_h186_stats.py --credentials /path/to/credentials.json --ha-json
```
JSON format:
```json
{
  "host": "<MODEM-LAN-IP>",
  "username": "admin",
  "password": "<MODEM-PASSWORD>"
}
```

### 2. Command-Line Arguments & Environment Variables
For interactive use or containerized setups:
```sh
# Using CLI parameters:
python3 zte_h186_stats.py --host <MODEM-LAN-IP> --user admin --password "<MODEM-PASSWORD>"

# Or via environment variables:
export ZTE_MODEM_HOST="<MODEM-LAN-IP>"
export ZTE_MODEM_USER="admin"
export ZTE_MODEM_PASSWORD="<MODEM-PASSWORD>"
python3 zte_h186_stats.py --ha-json
```

### 3. Encrypted Age Secrets (Maximum At-Rest Security)
For environments requiring secrets encryption at rest without plain credentials files, you can use `age`:

Run these helper commands to prompt and encrypt directly into `secrets/`:
```sh
./store-age-secret.sh zte-ipaddress
./store-age-secret.sh zte-admin-password
```
The helper creates `~/.config/age/keys.txt` (or respects `AGE_IDENTITY`) and stores encrypted `.age` files.

```sh
python3 zte_h186_stats.py --ha-json
```

### 4. Home Assistant UI Config Flow
When installed as a Home Assistant Integration (via HACS or `custom_components/zte_h186`):
1. In Home Assistant, navigate to **Settings > Devices & Services > Add Integration**.
2. Search for **ZTE H186 DSL Modem**.
3. Enter the modem IP address (`<MODEM-LAN-IP>`), username (`admin`), and password.
4. The integration automatically establishes a session, verifies connectivity, and creates 27 sensors and a diagnostic refresh button.

For detailed hardware port cabling (Red WAN, Yellow LAN, Grey DSL) and assigning a static management IP to the modem, see the [Cabling and Local Management Guide](HomeAssistant.md#verkabelung-und-lokale-verwaltung-des-modems).

## Requirements

- Python 3.10 or later
- Network access to the ZTE H186 modem web interface (default port 80)
- A ZTE H186 with the DSL status page enabled

## Run the Client

```sh
# Human-readable table:
python3 zte_h186_stats.py

# Raw XML values as JSON:
python3 zte_h186_stats.py --json

# Normalized Home Assistant JSON:
python3 zte_h186_stats.py --ha-json
```

## Troubleshooting

- `Erforderliches Secret fehlt`: create the missing value with the matching
  `store-age-secret.sh` purpose shown in the error.
- `age konnte ein Secret nicht entschlüsseln`: use the same private identity
  that was used when the encrypted file was created.
- `Das IP-Secret enthält keine gültige IP-Adresse`: create a new address file
  containing only a valid IPv4 or IPv6 address.
- `Router nicht erreichbar`: check local network access and the address file.
- Login or session errors: confirm the password and see the request order in
  [Protocol](PROTOCOL.md).