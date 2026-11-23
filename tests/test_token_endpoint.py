"""Regression tests for the login-token endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.zte_h186.api import ZteH186ApiClient, ZteH186ConnectionError

from .fake_http import LOGIN_PAGE, FakeResponse


async def test_token_endpoint_http_error_is_not_a_bad_password() -> None:
    """A failing token endpoint is a connection problem, not wrong credentials."""
    session = MagicMock()
    session.closed = False
    session.get.side_effect = [
        FakeResponse(LOGIN_PAGE),
        FakeResponse("<html>404 Not Found</html>", status=404),
    ]
    session.post.return_value = FakeResponse("")
    client = ZteH186ApiClient("192.168.10.2", "admin", "pw", session=session)

    with pytest.raises(ZteH186ConnectionError):
        await client.async_login()

    session.post.assert_not_called()
