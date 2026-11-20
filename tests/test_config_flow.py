"""Tests for the ZTE H186 config, reconfigure, reauth and options flows."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.api import ZteH186AuthError, ZteH186ConnectionError
from custom_components.zte_h186.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    CONF_USERNAME,
    DOMAIN,
)

from .conftest import MAC, SERIAL

USER_INPUT = {
    CONF_HOST: "192.168.10.2",
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "secret",
}


async def test_user_flow_success(hass: HomeAssistant, mock_client) -> None:
    """The happy path creates a config entry."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"ZTE H186 ({SERIAL})"
    assert result["data"] == {**USER_INPUT, CONF_SERIAL: SERIAL, CONF_MAC: MAC}
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert (entry.unique_id, entry.minor_version) == (SERIAL, 2)
    mock_client.close.assert_awaited()  # the validation session is logged out again


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (ZteH186AuthError("x"), "invalid_auth"),
        (ZteH186ConnectionError("x"), "cannot_connect"),
        (RuntimeError("x"), "unknown"),
    ],
)
async def test_user_flow_error_then_recovery(
    hass: HomeAssistant, mock_client, side_effect: Exception, error: str
) -> None:
    """Validation errors are shown, then the form recovers to success."""
    mock_client.async_login.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_client.async_login.side_effect = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_duplicate_aborts(
    hass: HomeAssistant, mock_client, mock_config_entry: MockConfigEntry
) -> None:
    """A second entry for the same host is rejected."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_flow(
    hass: HomeAssistant, mock_client, mock_config_entry: MockConfigEntry
) -> None:
    """Reconfigure updates the host on the existing entry."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.10.5", CONF_USERNAME: "admin", CONF_PASSWORD: "secret"},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "192.168.10.5"


async def test_reauth_flow(
    hass: HomeAssistant, mock_client, mock_config_entry: MockConfigEntry
) -> None:
    """Reauth asks for new credentials and updates the entry."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "newpass"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_PASSWORD] == "newpass"


async def test_options_flow(
    hass: HomeAssistant, mock_client, mock_config_entry: MockConfigEntry
) -> None:
    """The options flow updates the scan interval."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 120}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 120
