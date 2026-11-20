"""Parser and client tests against synthetic modem answers (``tests/fixtures``).

The files are made up: they follow the structure of the modem's answers, but every value is
invented. See docs/PROTOCOL.md for how to add an answer captured from a real modem.
"""

from __future__ import annotations

import pytest

from custom_components.zte_h186.api import (
    ZteH186ApiClient,
    ZteH186ProtocolError,
    parse_dsl_values,
)

from .fake_http import FIXTURES, fake_modem, fixture


def _client(session) -> ZteH186ApiClient:
    return ZteH186ApiClient("192.168.10.2", "admin", "secret", session=session)


def test_all_fixtures_exist_and_are_well_formed() -> None:
    names = {p.name for p in FIXTURES.glob("*.xml")}
    assert {
        "dsl_up.xml",
        "dsl_training.xml",
        "dsl_down.xml",
        "dsl_up_incomplete.xml",
        "device_info.xml",
        "session_timeout.xml",
    } <= names
    for name in names:
        values = ZteH186ApiClient._extract_xml_values(fixture(name))
        assert values["IF_ERRORSTR"]


def test_up_fixture_parses_every_value() -> None:
    values = ZteH186ApiClient._extract_xml_values(fixture("dsl_up.xml"))
    data, missing = parse_dsl_values(values)
    assert missing == []
    assert data.dsl_status == "Up"
    assert data.downstream_sync == pytest.approx(100.0)
    assert data.upstream_sync == pytest.approx(40.0)
    assert data.downstream_max == pytest.approx(120.0)
    assert data.downstream_snr == pytest.approx(9.5)
    assert data.upstream_attenuation == pytest.approx(13.0)
    assert data.downstream_power == pytest.approx(14.0)
    assert data.profile == "17a"
    assert data.modulation == "VDSL2_Vectoring"
    assert data.showtime == 86400
    assert (data.downstream_crc, data.upstream_crc) == (12, 3)
    assert (data.downstream_fec, data.upstream_fec) == (100, 200)


@pytest.mark.parametrize(
    ("name", "status"), [("dsl_training.xml", "Handshake"), ("dsl_down.xml", "Down")]
)
def test_training_and_down_fixtures_have_unknown_metrics(name: str, status: str) -> None:
    data, missing = parse_dsl_values(ZteH186ApiClient._extract_xml_values(fixture(name)))
    assert missing == []
    assert data.dsl_status == status
    assert data.downstream_sync is None
    assert data.downstream_snr is None
    assert data.profile is None


def test_incomplete_up_fixture_names_the_missing_values() -> None:
    data, missing = parse_dsl_values(
        ZteH186ApiClient._extract_xml_values(fixture("dsl_up_incomplete.xml"))
    )
    assert sorted(missing) == ["Downstream_current_rate", "Module_type"]
    assert data.downstream_sync is None
    assert data.upstream_sync == pytest.approx(40.0)


async def test_client_reads_the_up_fixture() -> None:
    data = await _client(fake_modem(fixture("dsl_up.xml"))).async_get_dsl_stats()
    assert data.dsl_status == "Up"
    assert data.downstream_sync == pytest.approx(100.0)


async def test_client_follows_the_line_through_its_states() -> None:
    """The same client sees Up, then Training, then Down, then Up again."""
    client = _client(
        fake_modem(
            fixture("dsl_up.xml"),
            fixture("dsl_training.xml"),
            fixture("dsl_down.xml"),
            fixture("dsl_up.xml"),
        )
    )
    states = [(await client.async_get_dsl_stats()).dsl_status for _ in range(4)]
    assert states == ["Up", "Handshake", "Down", "Up"]


async def test_client_logs_in_again_after_a_session_timeout() -> None:
    client = _client(fake_modem(fixture("session_timeout.xml"), fixture("dsl_up.xml")))
    data = await client.async_get_dsl_stats()
    assert data.dsl_status == "Up"


async def test_client_reads_the_device_information_fixture() -> None:
    session = fake_modem(fixture("dsl_up.xml"), device_info=fixture("device_info.xml"))
    info = await _client(session).async_get_device_info()
    assert info.serial_number == "ZTE0123456789A42"
    assert info.mac_address == "dc:f8:b9:00:11:22"
    assert info.model == "H186"
    assert info.software_version == "V1.0.0TY.1T2"
    assert info.dsl_version == "8B1017_8B0701"


async def test_client_rejects_a_session_timeout_that_does_not_go_away() -> None:
    session = fake_modem(fixture("session_timeout.xml"))
    with pytest.raises(ZteH186ProtocolError):
        await _client(session).async_get_device_info()
