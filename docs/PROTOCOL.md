# Modem Request Protocol

[English](en/Protocol.md) | [Deutsch](de/Protocol.md) | [Français](fr/Protocol.md) | [Español](es/Protocol.md)

The client uses the modem's existing web UI session and makes a read-only DSL
statistics request. The modem address and password are loaded from the local
encrypted files described in [Setup](SETUP.md).

## Request Sequence

All requests share one cookie jar:

1. Load the login page and decode its JavaScript session token.
2. Request the login token from
   `/function_module/login_module/login_page/logintoken_lua.lua`.
3. Submit the administrator name, the SHA-256 hash of the password followed
   by the login token, the login action, and the page session token.
4. Load the DSL status page:
   `getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp`.
5. Request `/common_page/internet_dsl_interface_lua.lua` with the same session
   and the status page as the HTTP referer.

Loading the status page between login and the data request is required to
establish the session state expected by the modem. A successful login and a
valid session cookie alone are not sufficient.

## Response Data

The endpoint returns XML records containing parameter names and values. The
client extracts current and attainable downstream/upstream rates, noise
margins, attenuation, profile, and modulation. Rates are reported in Mbit/s;
noise margins and attenuation are reported in dB.

The client validates the expected fields and fails with a concise error if the
router reports a session error or an incomplete response. It does not change
router configuration.