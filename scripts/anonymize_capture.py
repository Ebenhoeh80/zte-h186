"""Anonymize a capture of the modem's answers before it is shared or added to ``tests/fixtures``.

Replaces what identifies a modem or its owner with synthetic values: serial numbers, hardware (MAC)
addresses, IPv4 and IPv6 addresses, the names of Wi-Fi networks, session ids and the values of
credential-like parameters (password, key, token, user name). The same input value always becomes
the same synthetic value, so relations in the capture stay visible.

    python scripts/anonymize_capture.py capture.xml > tests/fixtures/new_answer.xml
    python scripts/anonymize_capture.py capture.xml -o clean.xml --serial ABC123
    python scripts/anonymize_capture.py capture.xml --replace "My ISP=ISP"

It is a safety net, not a guarantee: read the result before you publish it (see docs/PROTOCOL.md).
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable, Iterable
from functools import partial
from pathlib import Path
import re
import sys

_MAC = re.compile(r"(?<![0-9A-Fa-f:-])[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}(?![0-9A-Fa-f:-])")
_IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_HEX = r"[0-9A-Fa-f]{1,4}"
_IPV6 = re.compile(
    rf"(?<![0-9A-Fa-f:])(?:(?:{_HEX}:){{7}}{_HEX}|(?:{_HEX}:){{0,6}}:(?:{_HEX}(?::{_HEX}){{0,6}})?)"
    r"(?![0-9A-Fa-f:])"
)
_SID = re.compile(r"\bSID=[^;,\s\"'<]+")
# <Name>value</Name> and <ParaName>Name</ParaName><ParaValue>value</ParaValue>
_SERIAL_NAMES = r"SerialNumber|serial_number|SerialNo"
_SSID_NAMES = r"SSID|ESSID|WLANName|WifiName"
_SECRET_NAMES = (
    r"[A-Za-z_]*(?:Password|Passwd|PreSharedKey|PSK|Secret|Token|UserName|Username|PPPoEUser)"
    r"[A-Za-z_]*"
)


def _values(text: str, names: str) -> set[str]:
    """Return the values of the elements (or ParaName/ParaValue pairs) with these names."""
    found: set[str] = set()
    for match in re.finditer(rf"<(?:{names})>\s*([^<]+?)\s*</(?:{names})>", text):
        found.add(match.group(1))
    for match in re.finditer(
        rf"<ParaName>\s*(?:{names})\s*</ParaName>\s*<ParaValue>\s*([^<]+?)\s*</ParaValue>", text
    ):
        found.add(match.group(1))
    return {value for value in found if value}


def _synthetic_serial(n: int, *, width: int) -> str:
    """Return a serial number of the same length as the original (letters and digits only)."""
    return f"SYNTH{n:0{width}d}"


class _Mapper:
    """Give each distinct original value a stable synthetic value."""

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], str] = {}
        self.counts: Counter[str] = Counter()

    def get(self, kind: str, original: str, make: Callable[[int], str]) -> str:
        key = (kind, re.sub(r"[:-]", "", original.lower()) if kind == "mac" else original.lower())
        if key not in self._seen:
            self._seen[key] = make(len([k for k in self._seen if k[0] == kind]) + 1)
        self.counts[kind] += 1
        return self._seen[key]


def anonymize(
    text: str,
    *,
    serials: Iterable[str] = (),
    ssids: Iterable[str] = (),
    replacements: Iterable[tuple[str, str]] = (),
) -> tuple[str, Counter[str]]:
    """Return the anonymized text and how many values of each kind were replaced."""
    mapper = _Mapper()

    for old, new in replacements:
        if old:
            count = text.count(old)
            text = text.replace(old, new)
            mapper.counts["custom"] += count

    # Credential-like parameters first: their values vanish completely.
    def secret(match: re.Match[str]) -> str:
        mapper.counts["secret"] += 1
        return match.group("head") + "REDACTED" + match.group("tail")

    text = re.sub(
        rf"(?P<head><(?P<n>{_SECRET_NAMES})>\s*)[^<]*?(?P<tail>\s*</(?P=n)>)", secret, text
    )
    text = re.sub(
        rf"(?P<head><ParaName>\s*{_SECRET_NAMES}\s*</ParaName>\s*<ParaValue>)[^<]*"
        r"(?P<tail></ParaValue>)",
        secret,
        text,
    )

    def sid(_match: re.Match[str]) -> str:
        mapper.counts["sid"] += 1
        return "SID=SYNTHETICSID"

    text = _SID.sub(sid, text)

    serial_values = set(serials) | _values(text, _SERIAL_NAMES)
    for value in sorted(serial_values, key=len, reverse=True):
        width = max(len(value) - 5, 1)
        synthetic = mapper.get("serial", value, partial(_synthetic_serial, width=width))
        text = text.replace(value, synthetic)

    ssid_values = set(ssids) | _values(text, _SSID_NAMES)
    for value in sorted(ssid_values, key=len, reverse=True):
        text = text.replace(value, mapper.get("ssid", value, lambda n: f"SyntheticNet-{n}"))

    def mac(match: re.Match[str]) -> str:
        original = match.group(0)
        sep = ":" if ":" in original else "-"
        synthetic = mapper.get("mac", original, lambda n: f"02:00:00:00:00:{n:02x}")
        return synthetic.replace(":", sep)

    text = _MAC.sub(mac, text)

    def ipv4(match: re.Match[str]) -> str:
        if any(int(part) > 255 for part in match.group(0).split(".")):
            return match.group(0)  # a version number, not an address
        return mapper.get("ipv4", match.group(0), lambda n: f"192.0.2.{n}")

    text = _IPV4.sub(ipv4, text)
    text = _IPV6.sub(lambda m: mapper.get("ipv6", m.group(0), lambda n: f"2001:db8::{n:x}"), text)
    return text, mapper.counts


def main(argv: list[str] | None = None) -> int:
    """Anonymize the file given on the command line."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("capture", type=Path, help="the captured answer (XML, HTML or text)")
    parser.add_argument("-o", "--output", type=Path, help="write here instead of to stdout")
    parser.add_argument("--serial", action="append", default=[], help="a serial number to replace")
    parser.add_argument("--ssid", action="append", default=[], help="a Wi-Fi name to replace")
    parser.add_argument(
        "--replace", action="append", default=[], metavar="OLD=NEW", help="any other text"
    )
    args = parser.parse_args(argv)

    pairs = [tuple(item.split("=", 1)) for item in args.replace if "=" in item]
    text = args.capture.read_text(encoding="utf-8", errors="replace")
    clean, counts = anonymize(text, serials=args.serial, ssids=args.ssid, replacements=pairs)
    if args.output:
        args.output.write_text(clean, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(clean)
    summary = ", ".join(f"{kind}: {n}" for kind, n in sorted(counts.items())) or "nothing replaced"
    print(f"Replaced - {summary}. Read the result before you share it.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
