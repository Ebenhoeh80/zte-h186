"""Regression tests for accepted but mixed-case URL schemes."""

from __future__ import annotations

import pytest

from custom_components.zte_h186.api import ZteH186ApiClient


@pytest.mark.parametrize(
    ("host", "base_url"),
    [
        ("HTTP://192.168.10.2", "http://192.168.10.2"),
        ("Https://modem.lan", "https://modem.lan"),
        ("HTTP://[::1]:8080/", "http://[::1]:8080"),
    ],
)
def test_accepted_scheme_case_is_normalised(host: str, base_url: str) -> None:
    """A scheme accepted by validation must produce a usable request URL."""
    assert ZteH186ApiClient(host).base_url == base_url
