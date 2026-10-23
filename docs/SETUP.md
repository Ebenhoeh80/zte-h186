# Setup and Configuration

Each checkout requires its own modem address and administrator password. The
client deliberately has no default modem address and does not accept either
value through command-line arguments or environment variables. Both values
must be stored as encrypted age files in the project's `secrets/` directory.

## Requirements

- Python 3.10 or later
- `age` and `age-keygen`
- Network access from this machine to the modem's web interface
- A ZTE H186 with the DSL status page enabled

No Python packages need to be installed.

## Create Local Secrets

Run these commands from the project root. The helper prompts without echoing
the entered value and writes an encrypted file under `secrets/`:

```sh
./store-age-secret.sh zte-ipaddress
./store-age-secret.sh zte-admin-password
```

For the address prompt, enter only an IPv4 or IPv6 address, without a scheme,
port, path, or surrounding quotes. For the password prompt, enter the modem
administrator password. Do not place either value in source files, shell
arguments, environment variables, issue reports, or public logs.

The first invocation creates `~/.config/age/keys.txt` if it does not exist.
This is the private age identity used to decrypt the local files. Keep a
protected backup of it: without the matching identity, the encrypted files
cannot be recovered. If an identity already exists, the helper uses it.

The resulting filenames follow these patterns:

- `secrets/zte-ipaddress-<UTC timestamp>.age`
- `secrets/zte-admin-password-<UTC timestamp>.age`

The client uses the newest file matching each pattern. Create a new encrypted
file with the same purpose to replace a value. Remove obsolete local versions
only after confirming the new file works.

## Run the Client

```sh
python3 zte_h186_stats.py
python3 zte_h186_stats.py --json
```

Use `AGE_IDENTITY` to select a non-default private identity:

```sh
AGE_IDENTITY=/path/to/private/identity.txt python3 zte_h186_stats.py
```

The client decrypts the two files in memory, validates that the address is an
IP literal, logs in, loads the DSL status page, and then requests the DSL data.
It does not write decrypted values to disk.

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