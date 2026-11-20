# Security Policy

## Supported Versions

Security fixes are made in the latest release.

| Version | Supported          |
| ------- | ------------------ |
| 1.5.x   | :white_check_mark: |
| < 1.5.0 | :x:                |

## Threat model

The integration talks to the web interface of a ZTE H186 modem on your local network. The modem's own
firmware sets the limits:

| Topic | What happens | What to do |
| ----- | ------------ | ---------- |
| **No encryption** | The modem answers on plain HTTP. The login page, the login (the password is sent hashed with a one-time token, not as clear text, but everything else is readable) and every request run unencrypted. | Operate the modem and Home Assistant only in a **trusted LAN**. Anyone who can read the traffic between them sees the data and can take over the session. |
| **Session cookie** | The login returns a session id (`SID`) that every later request sends as a cookie, again over HTTP. Whoever has the cookie acts as the administrator until the session ends. | The integration keeps the id in memory only, never logs it in full and logs the session off when it is unloaded. Do not share logs or traces of the network traffic. |
| **Credentials** | Username and password are stored in Home Assistant's config entry (`.storage`), and so in every backup. | Protect access to Home Assistant and encrypt its backups. Use a password that is not used elsewhere. |
| **Exposure** | The modem's administration page must not be reachable from the internet. | Do not forward the modem's web interface (port 80) to the internet, and do not expose Home Assistant's access to it. |
| **Single session** | The modem allows one admin session at a time. A web login of yours can make the integration's login fail for a while (it asks for the password again only after repeated failures). | Close the modem's web interface when you are done. |
| **Diagnostics** | The download lists only known DSL values and version strings; address, serial number, hardware address, title and credentials are redacted. | Still check the file before sharing it. |

## Reporting a Vulnerability

If you discover a security vulnerability within this project:

1. **Do NOT open a public GitHub issue.**
2. Report the vulnerability privately via **GitHub Private Vulnerability Reporting** at:
   `https://github.com/Ebenhoeh80/zte-h186/security/advisories/new`
3. Include reproduction steps, the affected versions and, if you have one, a proof of concept. Remove
   serial numbers, hardware addresses and addresses from anything you attach (see
   [docs/PROTOCOL.md](docs/PROTOCOL.md) for the script that does it).

You get an answer within a few days, and we agree on a coordinated disclosure timeline together.

See also [docs/SECURITY.md](docs/SECURITY.md) for how the command-line tool handles its secrets.
