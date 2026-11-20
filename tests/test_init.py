"""Tests for ZTE H186 setup, unload, reauth and unique-ID migration."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.api import ZteH186AuthError, ZteH186ConnectionError
from custom_components.zte_h186.const import DOMAIN

from .conftest import SERIAL


async def test_setup_and_unload(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """A config entry sets up, creates entities, and unloads cleanly."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED

    ent_reg = er.async_get(hass)
    entities = er.async_entries_for_config_entry(ent_reg, mock_config_entry.entry_id)
    # 27 sensors + 2 binary sensors + 1 button
    assert len(entities) == 30
    # identified by the serial number (the entry of an older version is migrated at this setup)
    assert all(e.unique_id.startswith(SERIAL) for e in entities)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    mock_client.close.assert_awaited()


async def test_setup_auth_error_triggers_reauth(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """An auth error during the first refresh starts a reauth flow."""
    mock_client.async_get_dsl_stats.side_effect = ZteH186AuthError("rejected")
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == SOURCE_REAUTH for f in flows)


async def test_setup_connection_error_is_retried(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """A connection error during the first refresh schedules a retry."""
    mock_client.async_get_dsl_stats.side_effect = ZteH186ConnectionError("no route")
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unique_id_migration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """Legacy host-based unique IDs are migrated to the serial number (through the entry id)."""
    mock_config_entry.add_to_hass(hass)
    ent_reg = er.async_get(hass)
    legacy = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        "192.168.10.2_downstream_sync",
        config_entry=mock_config_entry,
    )
    assert legacy.unique_id == "192.168.10.2_downstream_sync"

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    migrated = ent_reg.async_get(legacy.entity_id)
    assert migrated is not None
    assert migrated.unique_id == f"{SERIAL}_downstream_sync"


async def test_device_identifier_migration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    """A legacy host-based device is rebound to the modem's serial number, not duplicated."""
    mock_config_entry.add_to_hass(hass)
    dev_reg = dr.async_get(hass)
    legacy = dev_reg.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, "192.168.10.2")},
        name="ZTE H186",
    )

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(dev_reg, mock_config_entry.entry_id)
    assert len(devices) == 1
    assert devices[0].id == legacy.id
    assert devices[0].identifiers == {(DOMAIN, SERIAL)}


def _reauth_flows(hass: HomeAssistant) -> list:
    return [
        f
        for f in hass.config_entries.flow.async_progress()
        if f["context"]["source"] == SOURCE_REAUTH
    ]


async def test_running_auth_errors_start_reauth_only_when_repeated(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client, dsl_data_up
) -> None:
    """One refused login while running is retried (busy session); two in a row start reauth."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = mock_config_entry.runtime_data

    mock_client.async_get_dsl_stats.side_effect = ZteH186AuthError("busy")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert coordinator.last_exception.translation_key == "auth_retry"
    assert not _reauth_flows(hass)

    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(_reauth_flows(hass)) == 1


async def test_running_auth_error_counter_is_reset_by_success(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client, dsl_data_up
) -> None:
    """A good poll (or another kind of failure) between two refused logins resets the count."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = mock_config_entry.runtime_data

    for outcome in (dsl_data_up, ZteH186ConnectionError("no route")):
        mock_client.async_get_dsl_stats.side_effect = ZteH186AuthError("busy")
        await coordinator.async_refresh()
        mock_client.async_get_dsl_stats.side_effect = None
        if isinstance(outcome, Exception):
            mock_client.async_get_dsl_stats.side_effect = outcome
        else:
            mock_client.async_get_dsl_stats.return_value = outcome
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert not _reauth_flows(hass)

    mock_client.async_get_dsl_stats.side_effect = ZteH186AuthError("busy")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not _reauth_flows(hass)
