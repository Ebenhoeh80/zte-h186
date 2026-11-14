"""Tests for ZTE H186 config-entry diagnostics."""

from __future__ import annotations

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from custom_components.zte_h186.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_redacts_credentials_and_includes_data(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """Diagnostics redact credentials/host and include the normalized data."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    entry_data = diag["entry"]["data"]
    assert entry_data[CONF_PASSWORD] == REDACTED
    assert entry_data[CONF_USERNAME] == REDACTED
    assert entry_data[CONF_HOST] == REDACTED

    assert diag["data"]["downstream_sync"] == 116.798
    assert diag["data"]["dsl_status"] == "Up"
    assert diag["last_update_success"] is True
