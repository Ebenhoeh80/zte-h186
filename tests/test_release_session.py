"""Tests for the release_session option (log off from the modem after each update)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.api import ZteH186AuthError, ZteH186ConnectionError
from custom_components.zte_h186.const import CONF_RELEASE_SESSION, CONF_SCAN_INTERVAL


def _with_release_session(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, *, enabled: bool
) -> None:
    """Add the fixture entry to hass with the option set (options change via the registry)."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_RELEASE_SESSION: enabled},
    )


async def test_release_session_is_off_by_default(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """Without the option the modem session is kept; no log-off after a poll."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    mock_client.async_logout.reset_mock()

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is True
    mock_client.async_logout.assert_not_awaited()


async def test_release_session_logs_off_after_each_successful_poll(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """With the option on, one successful poll logs off exactly once."""
    _with_release_session(hass, mock_config_entry, enabled=True)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    mock_client.async_logout.reset_mock()

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is True
    mock_client.async_logout.assert_awaited_once()


async def test_failing_logout_does_not_fail_the_poll(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """An exception from the log-off is only logged; the entities stay available."""
    _with_release_session(hass, mock_config_entry, enabled=True)
    mock_client.async_logout.side_effect = RuntimeError("log-off broke")
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is True
    assert mock_config_entry.state is ConfigEntryState.LOADED
    ent_reg = er.async_get(hass)
    entities = er.async_entries_for_config_entry(ent_reg, mock_config_entry.entry_id)
    sensor = next(e for e in entities if e.domain == "sensor")
    state = hass.states.get(sensor.entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE


async def test_connection_error_does_not_log_off(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """A connection error is not a session problem to release: no log-off is sent."""
    _with_release_session(hass, mock_config_entry, enabled=True)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    mock_client.async_logout.reset_mock()

    mock_client.async_get_dsl_stats.side_effect = ZteH186ConnectionError("no route")
    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
    mock_client.async_logout.assert_not_awaited()


async def test_auth_error_does_not_log_off(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """A refused login is not released either (the session belongs to someone else)."""
    _with_release_session(hass, mock_config_entry, enabled=True)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    mock_client.async_logout.reset_mock()

    mock_client.async_get_dsl_stats.side_effect = ZteH186AuthError("busy")
    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    mock_client.async_logout.assert_not_awaited()


async def test_options_flow_shows_and_saves_release_session(
    hass: HomeAssistant, mock_client, mock_config_entry: MockConfigEntry
) -> None:
    """The options form offers the switch, and True is saved."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    keys = [str(key) for key in result["data_schema"].schema]
    assert CONF_RELEASE_SESSION in keys

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 120, CONF_RELEASE_SESSION: True}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options[CONF_RELEASE_SESSION] is True
    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 120
