"""Regression tests: the SID cookie must never follow an HTTP redirect."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from custom_components.zte_h186.api import ZteH186ApiClient

from .fake_http import fake_modem, fixture


def _sid_gets(session: MagicMock) -> list[Any]:
    """Return the GET calls that carried the modem's admin session cookie."""
    return [
        call
        for call in session.get.call_args_list
        if "SID=" in call.kwargs.get("headers", {}).get("Cookie", "")
    ]


async def test_authenticated_gets_do_not_follow_redirects() -> None:
    """Every request with a SID header stays on the validated modem host."""
    session = fake_modem(fixture("dsl_up.xml"), device_info=fixture("device_info.xml"))
    client = ZteH186ApiClient("192.168.10.2", "admin", "pw", session=session)

    await client.async_get_dsl_stats()
    await client.async_get_device_info()

    calls = _sid_gets(session)
    assert len(calls) >= 4
    assert all(call.kwargs.get("allow_redirects") is False for call in calls)


async def test_retry_get_after_relogin_does_not_follow_redirects() -> None:
    """The DSL retry after an expired session is also pinned to the modem."""
    session = fake_modem(
        fixture("session_timeout.xml"),
        fixture("dsl_up.xml"),
        device_info=fixture("device_info.xml"),
    )
    client = ZteH186ApiClient("192.168.10.2", "admin", "pw", session=session)

    await client.async_get_dsl_stats()

    calls = _sid_gets(session)
    assert len(calls) >= 4
    assert all(call.kwargs.get("allow_redirects") is False for call in calls)
