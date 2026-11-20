"""Tests for the ZTE H186 refresh button."""

from __future__ import annotations

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.api import ZteH186ConnectionError
from custom_components.zte_h186.const import DOMAIN

from .conftest import SERIAL


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id(
        BUTTON_DOMAIN, DOMAIN, f"{SERIAL}_refresh_stats"
    )
    assert entity_id is not None
    return entity_id


async def test_pressing_the_button_polls_the_modem_now(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client, dsl_data_up
) -> None:
    """Pressing the button fetches fresh data immediately (it does not wait for the interval)."""
    entity_id = await _setup(hass, mock_config_entry)
    calls = mock_client.async_get_dsl_stats.await_count

    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert mock_client.async_get_dsl_stats.await_count == calls + 1


async def test_the_button_is_in_the_diagnostic_category_of_the_modem_device(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    entity_id = await _setup(hass, mock_config_entry)
    entry = er.async_get(hass).async_get(entity_id)
    assert entry is not None
    assert entry.entity_category == "diagnostic"
    assert entry.translation_key == "refresh_stats"
    assert entry.device_id is not None


async def test_the_button_is_unavailable_while_the_modem_cannot_be_read(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client
) -> None:
    entity_id = await _setup(hass, mock_config_entry)
    mock_client.async_get_dsl_stats.side_effect = ZteH186ConnectionError("no route")
    await mock_config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
