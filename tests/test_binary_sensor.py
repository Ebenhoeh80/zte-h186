"""Tests for the ZTE H186 binary sensors."""

from __future__ import annotations

from dataclasses import replace

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.api import (
    ZteH186ApiClient,
    ZteH186ConnectionError,
    ZteH186Data,
    parse_dsl_values,
)
from custom_components.zte_h186.const import DOMAIN

from .conftest import SERIAL
from .fake_http import fixture


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant, key: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id("binary_sensor", DOMAIN, f"{SERIAL}_{key}")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


@pytest.mark.parametrize(
    ("downstream", "upstream", "warning"),
    [(10.3, 6.8, STATE_OFF), (5.9, 8.0, STATE_ON), (9.0, 5.5, STATE_ON), (6.0, 6.0, STATE_OFF)],
)
async def test_line_noise_warning_threshold(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client,
    dsl_data_up: ZteH186Data,
    downstream: float,
    upstream: float,
    warning: str,
) -> None:
    """The warning is on when either SNR margin is below 6 dB."""
    mock_client.async_get_dsl_stats.return_value = replace(
        dsl_data_up, downstream_snr=downstream, upstream_snr=upstream
    )
    await _setup(hass, mock_config_entry)
    assert _state(hass, "line_noise_warning") == warning
    assert _state(hass, "dsl_link") == STATE_ON


async def test_link_is_off_for_an_up_line_without_sync_rate(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client,
    dsl_data_up: ZteH186Data,
) -> None:
    """Status Up with an unknown or zero rate is not a working link."""
    mock_client.async_get_dsl_stats.return_value = replace(dsl_data_up, downstream_sync=None)
    await _setup(hass, mock_config_entry)
    assert _state(hass, "dsl_link") == STATE_OFF


@pytest.mark.parametrize(
    ("name", "link"),
    [("dsl_up.xml", STATE_ON), ("dsl_training.xml", STATE_OFF), ("dsl_down.xml", STATE_OFF)],
)
async def test_link_follows_the_state_of_the_synthetic_answers(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client, name: str, link: str
) -> None:
    """The binary sensors follow what the (synthetic) answers say."""
    data, _ = parse_dsl_values(ZteH186ApiClient._extract_xml_values(fixture(name)))
    mock_client.async_get_dsl_stats.return_value = data
    await _setup(hass, mock_config_entry)
    assert _state(hass, "dsl_link") == link


@pytest.mark.parametrize("raw", ["Show Time", "show-time", "Connected "])
async def test_link_agrees_with_the_normalised_status_sensor(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client,
    dsl_data_up: ZteH186Data,
    raw: str,
) -> None:
    """Both entities must report a connected line for the same raw modem status."""
    mock_client.async_get_dsl_stats.return_value = replace(dsl_data_up, dsl_status=raw)
    await _setup(hass, mock_config_entry)

    status_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{SERIAL}_dsl_status")
    assert status_id is not None
    status = hass.states.get(status_id)
    assert status is not None
    assert status.state == "connected"
    assert _state(hass, "dsl_link") == STATE_ON


async def test_binary_sensors_become_unavailable_when_the_modem_is_unreachable(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """A failed poll makes the entities unavailable."""
    await _setup(hass, mock_config_entry)
    mock_client.async_get_dsl_stats.side_effect = ZteH186ConnectionError("no route")
    await mock_config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert _state(hass, "dsl_link") == STATE_UNAVAILABLE
    assert _state(hass, "line_noise_warning") == STATE_UNAVAILABLE
