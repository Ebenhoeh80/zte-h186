"""Tests for ZTE H186 config-entry diagnostics."""

from __future__ import annotations

from dataclasses import replace
import json

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.api import ZteH186ApiClient, ZteH186Data, ZteH186DeviceInfo
from custom_components.zte_h186.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from custom_components.zte_h186.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import MAC, SERIAL

# Synthetic raw answer: the line metrics plus things that must never reach a diagnostics file.
RAW_XML = f"""<html><ajax_response_xml_root>
<IF_ERRORSTR>SUCC</IF_ERRORSTR>
<OBJ_DSL_ID><Instance>
<ParaName>Status</ParaName><ParaValue>Up</ParaValue>
<ParaName>Downstream_current_rate</ParaName><ParaValue>116798</ParaValue>
<ParaName>WANAddress</ParaName><ParaValue>203.0.113.77</ParaValue>
<ParaName>PPPoEUser</ParaName><ParaValue>kunde-4711@example.invalid</ParaValue>
<ParaName>SSID</ParaName><ParaValue>MeinNetz</ParaValue>
<ParaName>SerialNumber</ParaName><ParaValue>{SERIAL}</ParaValue>
<ParaName>MACAddress</ParaName><ParaValue>{MAC.upper()}</ParaValue>
</Instance></OBJ_DSL_ID>
</ajax_response_xml_root></html>"""
LEAKS = ("203.0.113.77", "kunde-4711", "MeinNetz", SERIAL, MAC, MAC.upper(), "secret")


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


async def test_diagnostics_whole_output_has_no_identifiers(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client,
    device_info: ZteH186DeviceInfo,
    dsl_data_up: ZteH186Data,
) -> None:
    """Nothing that identifies the modem, its address or its owner is in the whole JSON."""
    raw = ZteH186ApiClient._extract_xml_values(RAW_XML)
    assert raw["WANAddress"] == "203.0.113.77"  # the prepared answer does contain them
    mock_client.async_get_dsl_stats.return_value = replace(dsl_data_up, raw_values=raw)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = mock_config_entry.runtime_data
    coordinator.last_exception = RuntimeError(
        f"Unable to reach modem at http://192.168.10.2: no route to 192.168.10.2 ({SERIAL}, {MAC})"
    )
    coordinator.last_update_success = False

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    text = json.dumps(diag, default=str)

    for leak in (*LEAKS, "192.168.10.2", mock_config_entry.title):
        assert leak.lower() not in text.lower(), leak
    # what is useful stays
    assert diag["data"]["raw_values"] == {
        "IF_ERRORSTR": "SUCC",
        "Status": "Up",
        "Downstream_current_rate": "116798",
    }
    assert set(diag["data"]["raw_other_keys"]) == {
        "MACAddress",
        "ParaName",
        "ParaValue",
        "PPPoEUser",
        "SSID",
        "SerialNumber",
        "WANAddress",
    }
    assert diag["device"]["software_version"] == device_info.software_version
    assert diag["device"]["hardware_version"] == device_info.hardware_version
    assert diag["device"]["dsl_version"] == device_info.dsl_version
    assert diag["device"]["serial_number"] == REDACTED
    assert diag["device"]["mac_address"] == REDACTED
    assert diag["last_exception"].startswith("RuntimeError: ")
    assert "http" not in diag["last_exception"]
