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

A value the modem leaves out is unknown (`None`), never a made-up number. While the line trains
or is down the modem omits the metrics by design. If it reports `Status=Up` but leaves out
required values, the client keeps what it got and logs one warning that names the missing
values. Only an answer that holds no DSL value at all, invalid XML, a modem error or a session
error is a failure. The table of keys, divisors and required values is `DSL_FIELDS` in
`custom_components/zte_h186/api.py`.

The client reads at most 512 KiB of a page, 4 KiB of the login token and 256 KiB of an XML
answer; a larger answer is refused. It does not change router configuration.

## Test fixtures and captures

`tests/fixtures/*.xml` holds **synthetic** answers (line up, training, down, up with missing
values, device information, session timeout). Every value is invented; tests parse them and
run the client against them.

To add an answer that a real modem sent (for example a firmware that behaves differently),
anonymize it first, then check it by eye:

```sh
python scripts/anonymize_capture.py capture.xml > tests/fixtures/new_answer.xml
```

The script replaces serial numbers, hardware (MAC) addresses, IPv4 and IPv6 addresses, the
names of Wi-Fi networks, session ids (`SID=`) and the values of credential-like parameters
(password, key, token, user name) with synthetic values; the same original always becomes the
same replacement. Add values it cannot know with `--serial`, `--ssid` or `--replace OLD=NEW`
(for example the name of your provider or a host name). It is a safety net: **read the result
before you share it** in an issue or pull request, and never share the unprocessed capture.
Do not add captures that contain anything personal.