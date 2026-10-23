#!/usr/bin/env python3
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only

"""Read DSL line statistics from a ZTE H186 modem."""

import argparse
import hashlib
import http.cookiejar
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


class RouterError(Exception):
    pass


def request(opener, url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with opener.open(req, timeout=15) as response:
            return response.status, response.read().decode("latin-1", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("latin-1", "replace")
    except urllib.error.URLError as error:
        raise RouterError(f"Router nicht erreichbar: {error.reason}") from error


def decode_session_token(page):
    match = re.search(
        r'_sessionTmpToken\s*=\s*"((?:\\x[0-9a-fA-F]{2})+)"', page
    )
    if not match:
        raise RouterError("Session-Token fehlt auf der Loginseite.")
    encoded = "".join(re.findall(r"\\x([0-9a-fA-F]{2})", match.group(1)))
    return bytes.fromhex(encoded).decode("ascii")


def extract_xml(response):
    match = re.search(
        r"<ajax_response_xml_root\b[^>]*>.*?</ajax_response_xml_root>",
        response,
        re.DOTALL,
    )
    if not match:
        raise RouterError("Routerantwort enthält kein erwartetes XML.")
    try:
        return ET.fromstring(match.group(0))
    except ET.ParseError as error:
        raise RouterError("Routerantwort enthält ungültiges XML.") from error


def xml_values(root):
    values = {}
    for element in root.iter():
        name = element.tag.rsplit("}", 1)[-1]
        if element.text and element.text.strip():
            values[name] = element.text.strip()
        if name == "Instance":
            parameter = None
            for child in element:
                field = child.tag.rsplit("}", 1)[-1]
                content = (child.text or "").strip()
                if field == "ParaName":
                    parameter = content
                elif field == "ParaValue" and parameter:
                    values[parameter] = content
                    parameter = None
    return values


def find_secret(secrets_dir, pattern):
    candidates = [
        path
        for path in secrets_dir.glob(pattern)
        if path.is_file() and not path.is_symlink()
    ]
    if not candidates:
        raise RouterError(f"Erforderliches Secret fehlt: secrets/{pattern}")
    return max(candidates, key=lambda path: path.name)


def load_secret(secret_file, identity):
    age = shutil.which("age")
    if not age:
        raise RouterError("Das Programm 'age' ist nicht installiert.")
    if not secret_file.is_file():
        raise RouterError(f"Secret-Datei nicht gefunden: {secret_file}")
    if not identity.is_file():
        raise RouterError(f"age-Identity nicht gefunden: {identity}")

    result = subprocess.run(
        [age, "-d", "-i", str(identity), str(secret_file)],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RouterError(
            "age konnte ein Secret nicht entschlüsseln. Prüfe, ob die Identity "
            "zu den Dateien in secrets/ gehört."
        )
    secret = result.stdout.rstrip(b"\r\n")
    if not secret:
        raise RouterError("Ein entschlüsseltes Secret ist leer.")
    return secret


def modem_url_from_ip(secret):
    try:
        address = ipaddress.ip_address(secret.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as error:
        raise RouterError("Das IP-Secret enthält keine gültige IP-Adresse.") from error
    host = f"[{address}]" if address.version == 6 else str(address)
    return f"http://{host}"


def fetch_stats(base_url, username, password):
    base_url = base_url.rstrip("/")
    root_url = base_url + "/"
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))

    status, login_page = request(opener, root_url)
    if status != 200:
        raise RouterError(f"Loginseite lieferte HTTP {status}.")
    session_token = decode_session_token(login_page)

    token_url = urllib.parse.urljoin(
        root_url, "function_module/login_module/login_page/logintoken_lua.lua"
    )
    status, token_response = request(
        opener,
        token_url,
        headers={"Referer": root_url},
    )
    token_root = extract_xml(token_response)
    login_token = (token_root.text or "").strip()
    if not login_token.isdigit():
        token_values = xml_values(token_root)
        error = token_values.get("IF_ERRORSTR", "unbekannter Fehler")
        raise RouterError(f"Login-Token konnte nicht gelesen werden: {error}")

    password_hash = hashlib.sha256(password + login_token.encode("ascii")).hexdigest()
    login_body = urllib.parse.urlencode(
        {
            "Username": username,
            "Password": password_hash,
            "action": "login",
            "_sessionTOKEN": session_token,
        }
    ).encode()
    status, _ = request(
        opener,
        root_url,
        data=login_body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": root_url,
        },
    )
    if status != 200 or not any(cookie.name == "SID" for cookie in cookies):
        raise RouterError("Login fehlgeschlagen; keine SID-Session erhalten.")

    status_path = (
        "getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp"
    )
    status_url = urllib.parse.urljoin(root_url, status_path)
    status, status_page = request(
        opener, status_url, headers={"Referer": root_url}
    )
    if status != 200 or "internet_dsl_interface_lua.lua" not in status_page:
        raise RouterError(f"DSL-Statusseite konnte nicht geladen werden (HTTP {status}).")

    endpoint = urllib.parse.urljoin(
        root_url, "common_page/internet_dsl_interface_lua.lua"
    )
    endpoint += "?_=" + urllib.parse.quote(str(int(time.time() * 1000)))
    status, response = request(
        opener,
        endpoint,
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Referer": status_url,
        },
    )
    values = xml_values(extract_xml(response))
    error = values.get("IF_ERRORSTR", "")
    if status != 200 or error not in ("", "SUCC"):
        raise RouterError(f"DSL-Abfrage fehlgeschlagen: {error or f'HTTP {status}'}")

    expected = (
        "Downstream_current_rate",
        "Upstream_current_rate",
        "Downstream_max_rate",
        "Upstream_max_rate",
        "Downstream_noise_margin",
        "Upstream_noise_margin",
        "Downstream_attenuation",
        "Upstream_attenuation",
        "CurrentProfile",
        "Module_type",
    )
    found = {name: value for name, value in values.items() if name in expected}
    missing = [name for name in expected if name not in found]
    if missing:
        raise RouterError("DSL-Antwort unvollständig; fehlend: " + ", ".join(missing))
    return found


def format_value(values, key, divisor, unit):
    value = float(values[key]) / divisor
    return f"{value:.1f} {unit}"


def main():
    parser = argparse.ArgumentParser(description="DSL-Statistiken vom ZTE H186 lesen")
    parser.add_argument(
        "--identity",
        type=Path,
        default=Path(
            os.environ.get(
                "AGE_IDENTITY", "~/.config/age/keys.txt"
            )
        ),
        help="age-Identity (Standard: ~/.config/age/keys.txt)",
    )
    parser.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    args = parser.parse_args()

    secrets_dir = Path(__file__).resolve().parent / "secrets"
    address_secret = b""
    password = b""
    try:
        identity = args.identity.expanduser()
        address_file = find_secret(secrets_dir, "zte-ipaddress-*.age")
        password_file = find_secret(secrets_dir, "zte-admin-password-*.age")
        address_secret = load_secret(address_file, identity)
        password = load_secret(password_file, identity)
        base_url = modem_url_from_ip(address_secret)
        values = fetch_stats(base_url, "admin", password)
    except RouterError as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    finally:
        address_secret = b""
        password = b""

    if args.json:
        print(json.dumps(values, ensure_ascii=False, indent=2))
    else:
        print(f"Downstream sync:     {format_value(values, 'Downstream_current_rate', 1000, 'Mbit/s')}")
        print(f"Upstream sync:       {format_value(values, 'Upstream_current_rate', 1000, 'Mbit/s')}")
        print(f"Downstream max:      {format_value(values, 'Downstream_max_rate', 1000, 'Mbit/s')}")
        print(f"Upstream max:        {format_value(values, 'Upstream_max_rate', 1000, 'Mbit/s')}")
        print(f"Downstream SNR:      {format_value(values, 'Downstream_noise_margin', 10, 'dB')}")
        print(f"Upstream SNR:        {format_value(values, 'Upstream_noise_margin', 10, 'dB')}")
        print(f"Downstream attenuation: {format_value(values, 'Downstream_attenuation', 10, 'dB')}")
        print(f"Upstream attenuation:   {format_value(values, 'Upstream_attenuation', 10, 'dB')}")
        print(f"Profile:             {values['CurrentProfile']}")
        print(f"Modulation:          {values['Module_type']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())