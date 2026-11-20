"""Tests for the size limits of the modem's answers and for the validation of the address."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.zte_h186.api import (
    MAX_PAGE_BYTES,
    MAX_TOKEN_BYTES,
    MAX_XML_BYTES,
    ZteH186ApiClient,
    ZteH186ProtocolError,
    _read_text,
    validate_host,
)

from .fake_http import FakeContent

LOGIN_HTML = '<script>var _sessionTmpToken = "\x61\x62";</script>'


class Resp:
    """A response with a body and the context-manager behaviour of aiohttp's."""

    def __init__(self, body: str, status: int = 200) -> None:
        self.status = status
        self.content = FakeContent(body)
        self.headers = MagicMock(getall=MagicMock(return_value=[]))
        self.cookies: dict = {}

    async def __aenter__(self) -> Resp:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def _client(session: MagicMock) -> ZteH186ApiClient:
    session.closed = False
    return ZteH186ApiClient("192.168.10.2", "admin", "secret", session=session)


async def test_a_body_up_to_the_limit_is_read() -> None:
    assert await _read_text(Resp("x" * 100), 100) == "x" * 100  # type: ignore[arg-type]


async def test_a_body_over_the_limit_is_refused() -> None:
    with pytest.raises(ZteH186ProtocolError):
        await _read_text(Resp("x" * 101), 100)  # type: ignore[arg-type]


async def test_an_oversized_login_page_is_refused() -> None:
    session = MagicMock()
    session.get.return_value = Resp("x" * (MAX_PAGE_BYTES + 1))
    with pytest.raises(ZteH186ProtocolError):
        await _client(session).async_login()


async def test_an_oversized_token_is_refused() -> None:
    session = MagicMock()
    session.get.side_effect = [Resp(LOGIN_HTML), Resp("1" * (MAX_TOKEN_BYTES + 1))]
    with pytest.raises(ZteH186ProtocolError):
        await _client(session).async_login()


async def test_an_oversized_status_answer_is_refused() -> None:
    session = MagicMock()
    client = _client(session)
    client._sid = "sid"
    client._is_authenticated = True
    session.get.return_value = Resp("<a>" * (MAX_XML_BYTES // 3 + 1))
    with pytest.raises(ZteH186ProtocolError):
        await client.async_get_dsl_stats()


async def test_an_oversized_login_page_has_no_model() -> None:
    session = MagicMock()
    session.get.return_value = Resp("<title>H186</title>" + "x" * MAX_PAGE_BYTES)
    assert await ZteH186ApiClient.async_probe_model("192.168.10.2", session) is None


@pytest.mark.parametrize(
    "value",
    [
        "192.168.10.2",
        " 192.168.10.2 ",
        "192.168.10.2:8080",
        "fe80::1",
        "[fe80::1]:80",
        "modem",
        "modem.fritz.box",
        "my_modem.lan",
        "http://192.168.10.2",
        "https://modem.lan:8443/",
        "HTTP://[::1]",
    ],
)
def test_usable_addresses_are_accepted(value: str) -> None:
    assert validate_host(value) == value.strip().rstrip("/")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "ftp://192.168.10.2",
        "file:///etc/passwd",
        "http://192.168.10.2/admin",
        "http://192.168.10.2/?x=1",
        "http://user:pw@192.168.10.2",
        "192.168.10.2/admin",
        "modem lan",
        "-modem",
        "mo$dem",
        "192.168.10.2:99999",
        "192.168.10.2:abc",
        "[fe80::1",
        "a" * 300,
        "http://",
    ],
)
def test_other_values_are_refused(value: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        validate_host(value)
