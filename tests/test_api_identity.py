"""The identity requests of the API client: device information, log-off and the login-page probe."""

from __future__ import annotations

from unittest.mock import MagicMock

import aiohttp
import pytest

from custom_components.zte_h186.api import (
    ZteH186ApiClient,
    ZteH186ConnectionError,
    ZteH186ProtocolError,
)

INFO_XML = """<ajax_response_xml_root>
<IF_ERRORSTR>SUCC</IF_ERRORSTR>
<ModelName>H186</ModelName>
<SerialNumber>ZTE0123456789A42</SerialNumber>
<MACAddress>DC:F8:B9:00:11:22</MACAddress>
<HardwareVer>V1.0.0</HardwareVer>
<SoftwareVer>V1.0.0TY.1T2</SoftwareVer>
<BootVer>V1.0.0</BootVer>
<ModelFirmwareVer>8B1017_8B0701</ModelFirmwareVer>
</ajax_response_xml_root>"""
EXPIRED_XML = (
    "<ajax_response_xml_root><IF_ERRORSTR>SessionTimeout</IF_ERRORSTR></ajax_response_xml_root>"
)


class Resp:
    """A response that works as an async context manager, like aiohttp's."""

    def __init__(self, status: int = 200, text: str = "") -> None:
        self.status = status
        self._text = text

    async def __aenter__(self) -> Resp:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def text(self, *args: object, **kwargs: object) -> str:
        return self._text

    async def read(self) -> bytes:
        return self._text.encode()


def _client(session: MagicMock) -> ZteH186ApiClient:
    client = ZteH186ApiClient("192.168.10.2", "admin", "secret", session=session)
    session.closed = False
    logins = []

    async def fake_login(_session: object) -> None:
        logins.append(1)
        client._sid = "sid"
        client._is_authenticated = True

    client._async_login_internal = fake_login  # type: ignore[method-assign]
    client.logins = logins  # type: ignore[attr-defined]
    return client


async def test_the_device_information_is_read_after_the_status_page() -> None:
    session = MagicMock()
    session.get.side_effect = [Resp(200, "<html>status</html>"), Resp(200, INFO_XML)]
    client = _client(session)
    info = await client.async_get_device_info()
    assert info.serial_number == "ZTE0123456789A42"
    assert info.mac_address == "dc:f8:b9:00:11:22"
    assert (info.model, info.hardware_version, info.software_version) == (
        "H186",
        "V1.0.0",
        "V1.0.0TY.1T2",
    )
    assert (info.boot_version, info.dsl_version) == ("V1.0.0", "8B1017_8B0701")
    page, data = (call.args[0] for call in session.get.call_args_list)
    assert "ManagDiag_StatusManag_t.lp" in page  # the page is requested first
    assert "/common_page/ManagReg_lua.lua" in data


async def test_an_expired_session_is_renewed_once() -> None:
    session = MagicMock()
    session.get.side_effect = [
        Resp(200, ""),
        Resp(200, EXPIRED_XML),
        Resp(200, ""),
        Resp(200, INFO_XML),
    ]
    client = _client(session)
    info = await client.async_get_device_info()
    assert info.serial_number == "ZTE0123456789A42"
    assert len(client.logins) == 2  # type: ignore[attr-defined]


async def test_a_session_that_stays_expired_is_an_error() -> None:
    session = MagicMock()
    session.get.side_effect = [Resp(200, ""), Resp(200, EXPIRED_XML)] * 2
    client = _client(session)
    with pytest.raises(ZteH186ProtocolError):
        await client.async_get_device_info()


async def test_an_answer_without_a_usable_serial_number_is_an_error() -> None:
    no_serial = INFO_XML.replace("ZTE0123456789A42", "")
    session = MagicMock()
    session.get.side_effect = [Resp(200, ""), Resp(200, no_serial)]
    with pytest.raises(ZteH186ProtocolError):
        await _client(session).async_get_device_info()


async def test_an_error_reported_by_the_modem_is_an_error() -> None:
    session = MagicMock()
    session.get.side_effect = [
        Resp(200, ""),
        Resp(200, INFO_XML.replace("SUCC", "SOMETHING_WRONG")),
    ]
    with pytest.raises(ZteH186ProtocolError):
        await _client(session).async_get_device_info()


async def test_an_unreachable_modem_is_a_connection_error() -> None:
    session = MagicMock()
    session.get.side_effect = aiohttp.ClientError("no route")
    with pytest.raises(ZteH186ConnectionError):
        await _client(session).async_get_device_info()


async def test_the_log_off_request_frees_the_modems_session() -> None:
    session = MagicMock()
    session.post.return_value = Resp(200, "")
    client = _client(session)
    client._sid = "sid"
    client._is_authenticated = True
    await client.async_logout()
    (call,) = session.post.call_args_list
    assert call.kwargs["data"]["IF_LogOff"] == "1"
    assert "SID=sid" in call.kwargs["headers"]["Cookie"]
    assert client._sid is None
    assert client._is_authenticated is False


async def test_logging_off_without_a_session_sends_nothing() -> None:
    session = MagicMock()
    client = _client(session)
    await client.async_logout()
    session.post.assert_not_called()


async def test_a_failed_log_off_is_not_an_error() -> None:
    session = MagicMock()
    session.post.side_effect = aiohttp.ClientError("gone")
    client = _client(session)
    client._sid = "sid"
    client._is_authenticated = True
    await client.async_logout()
    assert client._is_authenticated is False


async def test_closing_the_client_logs_off_first() -> None:
    session = MagicMock()
    session.post.return_value = Resp(200, "")
    client = _client(session)
    client._sid = "sid"
    client._is_authenticated = True
    await client.close()
    session.post.assert_called_once()


async def test_the_login_page_tells_the_model_without_a_login() -> None:
    session = MagicMock()
    # the real page writes its title as character references
    session.get.return_value = Resp(200, "<html><title>&#72;&#49;&#56;&#54;</title></html>")
    assert await ZteH186ApiClient.async_probe_model("192.168.10.2", session) == "H186"


@pytest.mark.parametrize(
    "response",
    [Resp(404, ""), Resp(200, "<html>no title</html>"), Resp(200, "<title> </title>")],
)
async def test_a_device_without_a_usable_login_page_has_no_model(response: Resp) -> None:
    session = MagicMock()
    session.get.return_value = response
    assert await ZteH186ApiClient.async_probe_model("192.168.10.2", session) is None


async def test_an_unreachable_device_has_no_model() -> None:
    session = MagicMock()
    session.get.side_effect = aiohttp.ClientError("no route")
    assert await ZteH186ApiClient.async_probe_model("192.168.10.2", session) is None


async def test_a_title_with_a_nonsense_reference_does_not_break_the_probe() -> None:
    session = MagicMock()
    session.get.return_value = Resp(200, "<title>&#99999999;H186&#72;</title>")
    model = await ZteH186ApiClient.async_probe_model("192.168.10.2", session)
    assert model is not None
    assert "H186" in model


async def test_the_probe_does_not_follow_redirects() -> None:
    session = MagicMock()
    session.get.return_value = Resp(200, "<title>H186</title>")
    await ZteH186ApiClient.async_probe_model("192.168.10.2", session)
    assert session.get.call_args.kwargs["allow_redirects"] is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("DC:F8:B9:00:11:22", "dc:f8:b9:00:11:22"),
        ("dc-f8-b9-00-11-22", "dc:f8:b9:00:11:22"),
        ("dcf8b9001122", "dc:f8:b9:00:11:22"),
        ("nonsense", None),
        (None, None),
    ],
)
def test_the_hardware_address_is_written_the_way_home_assistant_does(
    value: str | None, expected: str | None
) -> None:
    from custom_components.zte_h186.api import _normalise_mac

    assert _normalise_mac(value) == expected
