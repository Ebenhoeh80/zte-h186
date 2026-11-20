"""A minimal stand-in for the body of an aiohttp response."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock


class FakeContent:
    """What ``resp.content`` offers the client: the body in chunks."""

    def __init__(self, body: str | bytes) -> None:
        self._body = body.encode("latin-1", errors="replace") if isinstance(body, str) else body

    async def iter_chunked(self, size: int) -> AsyncIterator[bytes]:
        """Yield the body in chunks of at most ``size`` bytes."""
        for start in range(0, len(self._body), size):
            yield self._body[start : start + size]


class FakeResponse:
    """A response (async context manager) with a body, like aiohttp's."""

    def __init__(self, body: str = "", status: int = 200, sid: str | None = None) -> None:
        self.status = status
        self.content = FakeContent(body)
        self.headers = MagicMock(
            getall=MagicMock(return_value=[f"SID={sid}; path=/"] if sid else [])
        )
        self.cookies: dict[str, Any] = {"SID": MagicMock(value=sid)} if sid else {}

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


FIXTURES = Path(__file__).parent / "fixtures"
LOGIN_PAGE = '<html><title>H186</title><script>var _sessionTmpToken = "\x61\x62";</script></html>'
PRIMED_STATUS_PAGE = (
    '<html><script src="/common_page/internet_dsl_interface_lua.lua"></script></html>'
)


def fixture(name: str) -> str:
    """Return the text of a synthetic modem answer from ``tests/fixtures``."""
    return (FIXTURES / name).read_text(encoding="utf-8")


def fake_modem(*answers: str, device_info: str | None = None) -> MagicMock:
    """Return a session that plays the modem: the login handshake, then the given DSL answers.

    Each call of the DSL endpoint returns the next answer; the last one repeats. The device
    information endpoint returns ``device_info`` (the status page it needs is always answered).
    """
    session = MagicMock()
    session.closed = False
    remaining = list(answers)

    def get(url: str, **_kwargs: Any) -> FakeResponse:
        if "logintoken_lua" in url:
            return FakeResponse("12345678")
        if "internet_dsl_interface_lua.lua?" in url or url.endswith(
            "internet_dsl_interface_lua.lua"
        ):
            body = remaining.pop(0) if len(remaining) > 1 else remaining[0]
            return FakeResponse(body)
        if "ManagReg_lua" in url:
            return FakeResponse(device_info or "")
        if "ManagDiag_StatusManag" in url:
            return FakeResponse(PRIMED_STATUS_PAGE)
        if "Internet_AdminInternetStatus_DSL_t" in url:
            return FakeResponse(PRIMED_STATUS_PAGE)
        return FakeResponse(LOGIN_PAGE)

    session.get.side_effect = get
    session.post.return_value = FakeResponse("", sid="sid_synthetic")
    return session
