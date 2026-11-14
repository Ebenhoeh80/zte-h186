"""Tests for ZTE H186 sensor and binary-sensor states."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.const import DOMAIN, DSL_STATUS_OPTIONS
from custom_components.zte_h186.sensor import _normalize_dsl_status


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Up", "connected"),
        ("showtime", "connected"),
        ("Down", "disconnected"),
        ("Idle", "idle"),
        ("No Signal", "no_signal"),
        ("Disabled", "disabled"),
        ("Initializing", "initializing"),
        ("Handshake", "initializing"),
        ("something-weird", "disconnected"),
        (None, None),
    ],
)
def test_normalize_dsl_status(raw: str | None, expected: str | None) -> None:
    """Every raw modem status maps to a valid enum option (or None)."""
    result = _normalize_dsl_status(raw)
    assert result == expected
    assert result is None or result in DSL_STATUS_OPTIONS


def _state_getter(hass: HomeAssistant, entry: MockConfigEntry) -> Callable[[str, str], str | None]:
    ent_reg = er.async_get(hass)

    def get(platform: str, suffix: str) -> str | None:
        entity_id = ent_reg.async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}_{suffix}")
        assert entity_id is not None, f"entity for {suffix} not found"
        state = hass.states.get(entity_id)
        assert state is not None
        return state.state

    return get


async def test_sensor_states_line_up(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """With the line up, sensors report the normalized values."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    get = _state_getter(hass, mock_config_entry)
    assert get("sensor", "downstream_sync") == "116.798"
    assert get("sensor", "upstream_sync") == "36.999"
    assert get("sensor", "downstream_snr") == "10.3"
    # dsl_status is an enum sensor: the raw "Up" is normalized to "connected".
    assert get("sensor", "dsl_status") == "connected"
    assert get("sensor", "modulation") == "VDSL2_Vectoring"
    assert get("binary_sensor", "dsl_link") == STATE_ON
    assert get("binary_sensor", "line_noise_warning") == STATE_OFF


async def test_sensor_states_line_down_report_unknown(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client,
    dsl_data_down,
) -> None:
    """With the line down, missing metrics are unknown (not a misleading 0)."""
    mock_client.async_get_dsl_stats.return_value = dsl_data_down
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    get = _state_getter(hass, mock_config_entry)
    assert get("sensor", "downstream_sync") == STATE_UNKNOWN
    assert get("sensor", "downstream_snr") == STATE_UNKNOWN
    assert get("sensor", "downstream_capacity_ratio") == STATE_UNKNOWN
    assert get("sensor", "dsl_status") == "disconnected"
    # SNR unknown must not falsely trip the low-SNR warning
    assert get("binary_sensor", "line_noise_warning") == STATE_UNKNOWN
    assert get("binary_sensor", "dsl_link") == STATE_OFF
