#!/usr/bin/env python3
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only

"""Read DSL line statistics from a ZTE H186 modem (Full 26 parameters + HA JSON)."""

import argparse
from datetime import datetime, timezone
import hashlib
import http.cookiejar
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


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
    if isinstance(secret, bytes):
        secret = secret.decode("ascii", errors="replace")
    clean = secret.strip().rstrip("/")
    if clean.startswith("http://") or clean.startswith("https://"):
        return clean
    try:
        address = ipaddress.ip_address(clean)
    except ValueError as error:
        raise RouterError("Das IP-Secret enthält keine gültige IP-Adresse.") from error
    host = f"[{address}]" if address.version == 6 else str(address)
    return f"http://{host}"


def fetch_stats(base_url, username, password):
    if isinstance(password, str):
        password = password.encode("utf-8")
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

    # Validate the 10 mandatory fields
    required = (
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
    missing = [name for name in required if name not in values]
    if missing:
        raise RouterError("DSL-Antwort unvollständig; Pflichtfeld(er) fehlen: " + ", ".join(missing))

    # Return ALL values from the router (both required and optional 16 fields plus any vendor fields)
    return values


def normalize_to_ha(values):
    """Normalize raw router XML values to Home Assistant standard types and units."""
    def _float(key, div=1.0):
        v = values.get(key)
        if v is None or v == "":
            return None
        try:
            return round(float(v) / div, 1)
        except (ValueError, TypeError):
            return None

    def _int(key):
        v = values.get(key)
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    data = {
        "downstream_sync": _float("Downstream_current_rate", 1000.0),
        "upstream_sync": _float("Upstream_current_rate", 1000.0),
        "downstream_max": _float("Downstream_max_rate", 1000.0),
        "upstream_max": _float("Upstream_max_rate", 1000.0),
        "downstream_snr": _float("Downstream_noise_margin", 10.0),
        "upstream_snr": _float("Upstream_noise_margin", 10.0),
        "downstream_attenuation": _float("Downstream_attenuation", 10.0),
        "upstream_attenuation": _float("Upstream_attenuation", 10.0),
        "profile": values.get("CurrentProfile", ""),
        "modulation": values.get("Module_type", ""),
    }

    # Optional 16 parameters
    if "Status" in values:
        data["dsl_status"] = values["Status"]
    if "Downstream_power" in values:
        data["downstream_power"] = _float("Downstream_power", 10.0)
    if "Upstream_power" in values:
        data["upstream_power"] = _float("Upstream_power", 10.0)
    if "Data_path" in values:
        data["data_path"] = values["Data_path"]
    if "DownInterleavedepth" in values:
        data["downstream_interleave_depth"] = _int("DownInterleavedepth")
    if "UpInterleaveDepth" in values:
        data["upstream_interleave_depth"] = _int("UpInterleaveDepth")
    if "DownInterleaveDelay" in values:
        data["downstream_interleave_delay"] = _int("DownInterleaveDelay")
    if "UpInterleaveDelay" in values:
        data["upstream_interleave_delay"] = _int("UpInterleaveDelay")
    if "DownstreamInp" in values:
        data["downstream_inp"] = _float("DownstreamInp", 10.0)
    if "UpstreamInp" in values:
        data["upstream_inp"] = _float("UpstreamInp", 10.0)
    if "Showtime_start" in values:
        data["showtime"] = _int("Showtime_start")
    if "tLinkEncapsulationUsed" in values:
        data["link_encapsulation"] = values["tLinkEncapsulationUsed"]
    if "DownCrc_errors" in values:
        data["downstream_crc"] = _int("DownCrc_errors")
    if "UpCrc_errors" in values:
        data["upstream_crc"] = _int("UpCrc_errors")
    if "Fec_errors" in values:
        data["downstream_fec"] = _int("Fec_errors")
    if "Atuc_fec_errors" in values:
        data["upstream_fec"] = _int("Atuc_fec_errors")

    return {k: v for k, v in data.items() if v is not None}


def format_value(values, key, divisor, unit):
    val = values.get(key)
    if val is None or val == "":
        return "N/A"
    try:
        value = float(val) / divisor
        return f"{value:.1f} {unit}"
    except ValueError:
        return str(val)


def format_seconds(seconds_str):
    try:
        sec = int(seconds_str)
        d = sec // 86400
        h = (sec % 86400) // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        return f"{sec}s ({d}d {h}h {m}m {s}s)"
    except (ValueError, TypeError):
        return str(seconds_str)


def main():
    parser = argparse.ArgumentParser(description="DSL-Statistiken vom ZTE H186 lesen (vollständige 26 Parameter)")
    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("ZTE_HOST"),
        help="Router IP-Adresse oder Hostname (z.B. 192.168.1.1)",
    )
    parser.add_argument(
        "--user",
        type=str,
        default=os.environ.get("ZTE_USER", "admin"),
        help="Router Benutzername (Standard: admin)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=os.environ.get("ZTE_PASSWORD"),
        help="Router Web-Passwort",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        help="JSON-Datei mit host und password",
    )
    parser.add_argument(
        "--identity",
        type=Path,
        default=Path(os.environ.get("AGE_IDENTITY", "~/.config/age/keys.txt")),
        help="age-Identity für verschlüsselte secrets/ (Standard: ~/.config/age/keys.txt)",
    )
    parser.add_argument("--json", action="store_true", help="Rohdaten als XML-JSON ausgeben")
    parser.add_argument("--ha-json", action="store_true", help="Home Assistant normiertes JSON ausgeben")
    args = parser.parse_args()

    base_url = None
    username = args.user or "admin"
    password = None

    # Priority 1: JSON credentials file
    if args.credentials and args.credentials.is_file():
        with open(args.credentials, "r", encoding="utf-8") as f:
            cred = json.load(f)
            base_url = modem_url_from_ip(cred["host"])
            username = cred.get("username", username)
            password = cred["password"].encode("utf-8")

    # Priority 2: Direct arguments or environment variables
    elif args.host and args.password:
        base_url = modem_url_from_ip(args.host)
        password = args.password.encode("utf-8")

    # Priority 3: Age encrypted secrets
    else:
        secrets_dir = Path(__file__).resolve().parent / "secrets"
        try:
            identity = args.identity.expanduser()
            address_file = find_secret(secrets_dir, "zte-ipaddress-*.age")
            password_file = find_secret(secrets_dir, "zte-admin-password-*.age")
            address_secret = load_secret(address_file, identity)
            password = load_secret(password_file, identity)
            base_url = modem_url_from_ip(address_secret)
        except Exception as err:
            if not base_url or not password:
                print(f"Fehler: Keine Zugangsdaten angegeben (--host & --password, --credentials oder secrets/): {err}", file=sys.stderr)
                return 1

    try:
        values = fetch_stats(base_url, username, password)
    except RouterError as error:
        if args.ha_json:
            print(json.dumps({
                "status": "error",
                "sampled_at": None,
                "error_code": "router_error",
                "error_message": str(error),
                "data": {}
            }, indent=2))
            return 0
        print(f"Fehler: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(values, ensure_ascii=False, indent=2))
    elif args.ha_json:
        ha_data = normalize_to_ha(values)
        output = {
            "status": "ok",
            "sampled_at": datetime.now(timezone.utc).isoformat(),
            "data": ha_data
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("==================================================")
        print("ZTE H186 DSL STATISTIKEN (26 Parameter)")
        print("==================================================")
        print(f"Router Status:       {values.get('Status', 'N/A')}")
        print(f"Modulation:          {values.get('Module_type', 'N/A')}")
        print(f"Profil:              {values.get('CurrentProfile', 'N/A')}")
        print(f"Datenpfad:           {values.get('Data_path', 'N/A')}")
        print(f"Link-Kapselung:      {values.get('tLinkEncapsulationUsed', 'N/A')}")
        print("--------------------------------------------------")
        print(f"Downstream sync:     {format_value(values, 'Downstream_current_rate', 1000, 'Mbit/s')}")
        print(f"Upstream sync:       {format_value(values, 'Upstream_current_rate', 1000, 'Mbit/s')}")
        print(f"Downstream max:      {format_value(values, 'Downstream_max_rate', 1000, 'Mbit/s')}")
        print(f"Upstream max:        {format_value(values, 'Upstream_max_rate', 1000, 'Mbit/s')}")
        print("--------------------------------------------------")
        print(f"Downstream SNR:      {format_value(values, 'Downstream_noise_margin', 10, 'dB')}")
        print(f"Upstream SNR:        {format_value(values, 'Upstream_noise_margin', 10, 'dB')}")
        print(f"Downstream Dämpfung: {format_value(values, 'Downstream_attenuation', 10, 'dB')}")
        print(f"Upstream Dämpfung:   {format_value(values, 'Upstream_attenuation', 10, 'dB')}")
        print(f"Downstream Leistung: {format_value(values, 'Downstream_power', 10, 'dBm')}")
        print(f"Upstream Leistung:   {format_value(values, 'Upstream_power', 10, 'dBm')}")
        print("--------------------------------------------------")
        print(f"Interleave Delay:    Down {values.get('DownInterleaveDelay', 'N/A')} ms / Up {values.get('UpInterleaveDelay', 'N/A')} ms")
        print(f"Interleave Tiefe:    Down {values.get('DownInterleavedepth', 'N/A')} / Up {values.get('UpInterleaveDepth', 'N/A')}")
        print(f"INP (Impulsschutz):  Down {format_value(values, 'DownstreamInp', 10, 'Symbole')} / Up {format_value(values, 'UpstreamInp', 10, 'Symbole')}")
        print(f"Showtime (Uptime):   {format_seconds(values.get('Showtime_start'))}")
        print("--------------------------------------------------")
        print(f"CRC Fehler:          Down {values.get('DownCrc_errors', '0')} / Up {values.get('UpCrc_errors', '0')}")
        print(f"FEC Fehler:          Down {values.get('Fec_errors', '0')} / Up {values.get('Atuc_fec_errors', '0')}")
        print("==================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())