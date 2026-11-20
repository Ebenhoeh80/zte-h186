"""Tests for the capture anonymizer (scripts/anonymize_capture.py)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "anonymize_capture",
    Path(__file__).resolve().parent.parent / "scripts" / "anonymize_capture.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
anonymize_capture = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(anonymize_capture)

# Made-up "real" values: the point is that none of them survives.
CAPTURE = """<ajax_response_xml_root>
<IF_ERRORSTR>SUCC</IF_ERRORSTR>
<Instance>
<ParaName>SerialNumber</ParaName><ParaValue>ZTEXYZ123456789</ParaValue>
<ParaName>MACAddress</ParaName><ParaValue>AA:BB:CC:11:22:33</ParaValue>
<ParaName>WANIP</ParaName><ParaValue>198.51.100.23</ParaValue>
<ParaName>LANIP</ParaName><ParaValue>10.1.2.3</ParaValue>
<ParaName>SSID</ParaName><ParaValue>FamilieMuster-5G</ParaValue>
<ParaName>PPPoEUserName</ParaName><ParaValue>kunde4711@isp.invalid</ParaValue>
<ParaName>WLANPreSharedKey</ParaName><ParaValue>geheim-geheim</ParaValue>
<ParaName>SoftwareVer</ParaName><ParaValue>V1.0.0TY.1T2</ParaValue>
<ParaName>IPv6</ParaName><ParaValue>2001:db8:abcd:12::1</ParaValue>
</Instance>
<SerialNumber>ZTEXYZ123456789</SerialNumber>
Set-Cookie: SID=0123456789abcdef; path=/
peer aa-bb-cc-11-22-33 and again AA:BB:CC:11:22:33
</ajax_response_xml_root>"""
SECRETS = (
    "ZTEXYZ123456789",
    "AA:BB:CC:11:22:33",
    "aa-bb-cc-11-22-33",
    "198.51.100.23",
    "10.1.2.3",
    "FamilieMuster",
    "kunde4711",
    "geheim",
    "0123456789abcdef",
    "2001:db8:abcd",
)


def test_every_identifier_is_replaced() -> None:
    clean, counts = anonymize_capture.anonymize(CAPTURE)
    for secret in SECRETS:
        assert secret.lower() not in clean.lower(), secret
    assert counts["serial"] == 1  # one distinct serial number
    assert counts["mac"] == 3
    assert counts["secret"] == 2
    assert counts["sid"] == 1


def test_values_that_are_not_identifiers_stay() -> None:
    clean, _ = anonymize_capture.anonymize(CAPTURE)
    assert "V1.0.0TY.1T2" in clean  # a version, not an address
    assert "<IF_ERRORSTR>SUCC</IF_ERRORSTR>" in clean


def test_the_same_value_gets_the_same_replacement() -> None:
    clean, _ = anonymize_capture.anonymize(CAPTURE)
    assert clean.count("02:00:00:00:00:01") == 2
    assert "02-00-00-00-00-01" in clean  # the separator of the original is kept
    assert clean.count("SYNTH0000000001") == 2


def test_the_serial_is_still_a_valid_serial_number() -> None:
    import re

    clean, _ = anonymize_capture.anonymize(CAPTURE)
    match = re.search(r"<SerialNumber>([^<]+)</SerialNumber>", clean)
    assert match is not None
    assert re.fullmatch(r"[A-Za-z0-9]{6,32}", match.group(1))
    assert len(match.group(1)) == len("ZTEXYZ123456789")


def test_extra_values_and_replacements() -> None:
    clean, counts = anonymize_capture.anonymize(
        "Anschluss von Familie Muster, Kunde 4711; serial X1Y2Z3W4",
        serials=["X1Y2Z3W4"],
        replacements=[("Familie Muster", "Owner")],
    )
    assert "Muster" not in clean
    assert "X1Y2Z3W4" not in clean
    assert counts["custom"] == 1


def test_the_command_line_writes_the_result(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    source = tmp_path / "capture.xml"
    source.write_text(CAPTURE, encoding="utf-8")
    target = tmp_path / "clean.xml"
    assert anonymize_capture.main([str(source), "-o", str(target)]) == 0
    assert "ZTEXYZ123456789" not in target.read_text(encoding="utf-8")
    assert "Read the result" in capsys.readouterr().err
