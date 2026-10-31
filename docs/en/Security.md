# Security and Public Releases

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](Security.md) | [Deutsch](../de/Security.md) | [Français](../fr/Security.md) | [Español](../es/Security.md)

## Secret Handling

The modem address and administrator password belong in encrypted files under
`secrets/`, created with `store-age-secret.sh` (or securely managed in Home Assistant ConfigEntries).
The repository ignores `.age` files and local contents of `secrets/`.
The helper creates the directory on first use. Do not force-add encrypted files or add plaintext
configuration files to the repository.

The private age identity at `~/.config/age/keys.txt` is not a public key. It
must remain private and must not be committed, uploaded, pasted into issues, or
shared with other users. Sharing an encrypted secret file without its matching
private identity does not let another user decrypt it. Each user should create
their own local secrets and identity.

Before publishing, verify that secret files are ignored:

```sh
git check-ignore secrets/zte-ipaddress-example.age
git check-ignore secrets/zte-admin-password-example.age
```

The example names above are placeholders; do not create files containing real
credentials for this check. Review staged files before every commit.

## Runtime Behavior

The client decrypts the address and password into process memory. The password
is hashed with the modem's login token before submission; the plaintext
password is not sent as an HTTP form value or written to a file by this client.
The modem session cookie is held in an in-memory cookie jar. Error messages do
not print secret values.

The modem exposes its web interface over unencrypted HTTP. Run the client
only on a trusted local network and do not expose the modem administration interface
to untrusted networks or the public internet. DSL statistics can also reveal information
about a subscriber line; treat captured output and diagnostic logs as private.

If an identity or password is exposed, replace the modem password immediately, create a
new local age identity as appropriate, and re-encrypt the local secrets.
