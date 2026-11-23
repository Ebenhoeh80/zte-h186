"""Regression tests for a session that stays expired after re-authentication."""

from __future__ import annotations

import pytest

from custom_components.zte_h186.api import ZteH186ApiClient, ZteH186AuthError

from .fake_http import fake_modem, fixture


async def test_persistent_session_timeout_is_an_auth_error() -> None:
    """A second SessionTimeout after re-login must start reauth, not report a protocol error."""
    session = fake_modem(fixture("session_timeout.xml"), fixture("session_timeout.xml"))
    client = ZteH186ApiClient("192.168.10.2", "admin", "pw", session=session)

    with pytest.raises(ZteH186AuthError):
        await client.async_get_dsl_stats()
