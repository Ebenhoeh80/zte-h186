"""The identity of the modem is its serial number: entry, title, device, entities, flows and
discovery."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import (
    SOURCE_DHCP,
    SOURCE_USER,
    ConfigEntryState,
)
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186 import async_migrate_entry
from custom_components.zte_h186.api import (
    ZteH186ConnectionError,
    ZteH186ProtocolError,
)
from custom_components.zte_h186.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SERIAL,
    CONF_USERNAME,
    DOMAIN,
)
from custom_components.zte_h186.identity import is_generated_title

from .conftest import MAC, SERIAL

HOST = "192.168.10.2"
NEW_HOST = "192.168.10.77"
TITLE = f"ZTE H186 ({SERIAL})"
OTHER_SERIAL = "ZTE9999999999Z99"


def _legacy(*, title: str | None = None) -> MockConfigEntry:
    """An entry as versions up to 1.4.1 made it: the address is its identity and in its title."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=title or f"ZTE H186 ({HOST})",
        unique_id=HOST,
        data={CONF_HOST: HOST, CONF_USERNAME: "admin", CONF_PASSWORD: "secret"},
        version=1,
        minor_version=1,
    )


def _modern(host: str = HOST) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        unique_id=SERIAL,
        data={
            CONF_HOST: host,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
            CONF_SERIAL: SERIAL,
            CONF_MAC: MAC,
        },
        version=1,
        minor_version=2,
    )


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


def _snapshot(hass: HomeAssistant, entry: MockConfigEntry) -> tuple[set[str], set[str]]:
    entities = {
        e.entity_id for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }
    devices = {d.id for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)}
    return entities, devices


# ------------------------------------------------------------------ migration


async def test_an_entry_of_an_older_version_is_migrated_without_losing_entities(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _legacy()
    await _setup(hass, entry)
    entities, devices = _snapshot(hass, entry)
    assert len(entities) == 30
    assert len(devices) == 1

    # put it back into the old shape (as it was before the update of the integration) and load it
    # again
    hass.config_entries.async_update_entry(
        entry,
        unique_id=HOST,
        title=f"ZTE H186 ({HOST})",
        minor_version=1,
        data={k: v for k, v in entry.data.items() if k not in (CONF_SERIAL, CONF_MAC)},
    )
    ent_reg = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        ent_reg.async_update_entity(
            entity.entity_id, new_unique_id=entity.unique_id.replace(SERIAL, entry.entry_id)
        )
    dev_reg = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        dev_reg.async_update_device(device.id, new_identifiers={(DOMAIN, entry.entry_id)})
    await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (entry.unique_id, entry.title, entry.minor_version) == (SERIAL, TITLE, 2)
    assert entry.data[CONF_SERIAL] == SERIAL
    assert entry.data[CONF_MAC] == MAC
    assert _snapshot(hass, entry) == (entities, devices)  # the same entity ids and the same device
    assert all(
        e.unique_id.startswith(f"{SERIAL}_")
        for e in er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    )
    (device,) = dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
    assert device.identifiers == {(DOMAIN, SERIAL)}
    assert (device.serial_number, device.model, device.sw_version) == (
        SERIAL,
        "H186",
        "V1.0.0TY.1T2",
    )


async def test_a_title_chosen_by_the_user_survives_the_migration(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _legacy(title="Modem Keller")
    await _setup(hass, entry)
    assert entry.title == "Modem Keller"
    assert entry.unique_id == SERIAL


@pytest.mark.parametrize("title", ["ZTE H186 (Wohnzimmer)", "ZTE H186 (Keller)"])
async def test_a_parenthesised_user_title_is_not_overwritten(
    hass: HomeAssistant, mock_client, title: str
) -> None:
    """Only the old address form is generated; a name in brackets belongs to the user."""
    assert not is_generated_title(title)
    entry = _legacy(title=title)
    await _setup(hass, entry)
    assert entry.title == title
    assert entry.unique_id == SERIAL


async def test_a_modem_that_cannot_report_its_serial_keeps_the_old_identity_until_it_can(
    hass: HomeAssistant, mock_client, device_info
) -> None:
    mock_client.async_get_device_info.side_effect = ZteH186ProtocolError("busy")
    entry = _legacy()
    await _setup(hass, entry)
    assert (entry.unique_id, entry.minor_version) == (HOST, 1)  # nothing to migrate to yet

    mock_client.async_get_device_info.side_effect = None
    mock_client.async_get_device_info.return_value = device_info
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert (entry.unique_id, entry.minor_version) == (SERIAL, 2)


async def test_an_identity_overwritten_by_an_older_version_is_put_right(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(entry, unique_id=HOST)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.unique_id == SERIAL


async def test_migrating_twice_changes_nothing_more(hass: HomeAssistant) -> None:
    entry = _legacy()
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry)
    assert await async_migrate_entry(hass, entry)
    assert (entry.unique_id, entry.minor_version) == (
        HOST,
        1,
    )  # the serial number comes from the modem at setup


async def test_an_entry_of_a_newer_major_version_is_refused(
    hass: HomeAssistant, mock_client
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=_modern().data, version=2)
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.MIGRATION_ERROR


# ------------------------------------------------------------------ the modem behind the address
# changes


async def test_another_modem_at_the_saved_address_is_not_taken_for_ours(
    hass: HomeAssistant, mock_client, device_info
) -> None:
    entry = _modern()
    entry.add_to_hass(hass)
    mock_client.async_get_device_info.return_value = type(device_info)(
        serial_number=OTHER_SERIAL, mac_address="dc:f8:b9:ff:ff:ff"
    )
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert (entry.unique_id, entry.data[CONF_SERIAL]) == (SERIAL, SERIAL)
    assert dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id) == []
    mock_client.close.assert_awaited()  # a failed setup must not keep the modem's single session


async def test_a_second_entry_for_the_same_modem_does_not_run(
    hass: HomeAssistant, mock_client
) -> None:
    first = _modern()
    await _setup(hass, first)
    second = _legacy()
    second.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(second.entry_id)
    assert second.state is ConfigEntryState.SETUP_ERROR
    assert first.state is ConfigEntryState.LOADED
    assert dr.async_entries_for_config_entry(dr.async_get(hass), second.entry_id) == []
    assert er.async_entries_for_config_entry(er.async_get(hass), second.entry_id) == []
    assert second.unique_id == HOST  # not taken over; the first entry owns the serial number


async def test_a_failed_setup_logs_out_of_the_modem(hass: HomeAssistant, mock_client) -> None:
    mock_client.async_get_dsl_stats.side_effect = ZteH186ConnectionError("no route")
    entry = _legacy()
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    mock_client.close.assert_awaited()


# ------------------------------------------------------------------ the user flow


async def test_adding_a_known_modem_under_another_address_updates_the_address(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: NEW_HOST, CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == NEW_HOST
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def test_the_session_of_a_running_entry_is_released_for_the_check(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
    )
    mock_client.async_logout.assert_awaited()  # the modem allows one admin session at a time


async def test_a_modem_without_a_serial_number_is_not_accepted(
    hass: HomeAssistant, mock_client
) -> None:
    mock_client.async_get_device_info.side_effect = ZteH186ProtocolError("no serial")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
    )
    assert result["errors"] == {"base": "cannot_connect"}


# ------------------------------------------------------------------ reconfigure and reauth


async def test_reconfigure_keeps_the_identity_and_changes_the_address(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    entities, devices = _snapshot(hass, entry)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: NEW_HOST, CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == NEW_HOST
    assert (entry.unique_id, entry.title) == (SERIAL, TITLE)
    assert _snapshot(hass, entry) == (entities, devices)
    mock_client.async_logout.assert_awaited()  # its running session was released for the check


async def test_reconfigure_refuses_a_different_modem(
    hass: HomeAssistant, mock_client, device_info
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    mock_client.async_get_device_info.return_value = type(device_info)(serial_number=OTHER_SERIAL)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: NEW_HOST, CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert entry.data[CONF_HOST] == HOST


async def test_reconfigure_adopts_the_serial_number_for_an_entry_of_an_older_version(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _legacy()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: NEW_HOST, CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert (entry.unique_id, entry.data[CONF_SERIAL], entry.title) == (SERIAL, SERIAL, TITLE)


async def test_reauth_refuses_a_different_modem(
    hass: HomeAssistant, mock_client, device_info
) -> None:
    entry = _modern()
    entry.add_to_hass(hass)
    mock_client.async_get_device_info.return_value = type(device_info)(serial_number=OTHER_SERIAL)
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "newpass"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert entry.data[CONF_PASSWORD] == "secret"


# ------------------------------------------------------------------ DHCP discovery


def _dhcp(ip: str, mac: str = "dcf8b9001122") -> DhcpServiceInfo:
    return DhcpServiceInfo(ip=ip, hostname="h186", macaddress=mac)


async def test_dhcp_follows_a_known_modem_to_its_new_address(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    first = entry.runtime_data
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=_dhcp(NEW_HOST)
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == NEW_HOST
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not first  # reloaded once


async def test_dhcp_offers_an_unknown_h186_with_its_address_prefilled(
    hass: HomeAssistant, mock_client
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=_dhcp(NEW_HOST)
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    host_key = next(key for key in result["data_schema"].schema if key == CONF_HOST)
    assert host_key.description["suggested_value"] == NEW_HOST


async def test_dhcp_ignores_a_device_that_is_not_an_h186(hass: HomeAssistant, mock_client) -> None:
    with patch(
        "custom_components.zte_h186.config_flow.ZteH186ApiClient.async_probe_model",
        AsyncMock(return_value="Printer"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_DHCP}, data=_dhcp(NEW_HOST)
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_dhcp_does_not_contact_an_address_that_is_set_up(
    hass: HomeAssistant, mock_client
) -> None:
    await _setup(hass, _modern())
    with patch(
        "custom_components.zte_h186.config_flow.ZteH186ApiClient.async_probe_model", AsyncMock()
    ) as probe:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_DHCP}, data=_dhcp(HOST, "aabbccddeeff")
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    probe.assert_not_called()


# ------------------------------------------------------------------ the title helpers (pure)


@pytest.mark.parametrize("title", ["ZTE H186 (192.168.10.2)", f"ZTE H186 {SERIAL}", "ZTE H186"])
def test_titles_made_by_the_integration_are_recognised(title: str) -> None:
    from custom_components.zte_h186.identity import is_generated_title

    assert is_generated_title(title)


@pytest.mark.parametrize(
    "title",
    [
        "Modem Keller",
        "ZTE H186 DSL Modem Keller",
        "my ZTE H186 (x)",
        "",
        "ZTE H186 Keller",
        "ZTE H186 Wohnzimmer",
        "ZTE H186 Modem1",
    ],
)
def test_titles_chosen_by_the_user_are_left_alone(title: str) -> None:
    from custom_components.zte_h186.identity import is_generated_title

    assert not is_generated_title(title)


def test_the_identity_key_is_the_serial_number_or_the_entry_id_until_it_is_known() -> None:
    from custom_components.zte_h186.identity import identity_key

    assert identity_key("entry1", {CONF_SERIAL: SERIAL}) == SERIAL
    assert identity_key("entry1", {}) == "entry1"
    assert MagicMock  # imported for the discovery tests


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("192.168.10.2", "http://192.168.10.2/"),
        ("Modem.Local", "modem.local."),
        ("fe80::1", "[FE80:0:0:0:0:0:0:1]"),
    ],
)
def test_the_same_host_is_recognised_in_other_spellings(first: str, second: str) -> None:
    from custom_components.zte_h186.identity import same_host

    assert same_host(first, second)
    assert not same_host(first, "192.168.10.99")


# ------------------------------------------------------------------ registries (heal, clash)


def _to_old_keys(hass: HomeAssistant, entry: MockConfigEntry, key: str) -> None:
    ent_reg = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        ent_reg.async_update_entity(
            entity.entity_id, new_unique_id=entity.unique_id.replace(SERIAL, key)
        )
    dev_reg = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        dev_reg.async_update_device(device.id, new_identifiers={(DOMAIN, key)})


async def test_a_reconfigured_entry_of_an_older_version_keeps_its_entities(
    hass: HomeAssistant, mock_client
) -> None:
    """The reconfigure writes the serial number first; the registries still follow at the reload."""
    entry = _legacy()
    await _setup(hass, entry)
    entities, devices = _snapshot(hass, entry)
    _to_old_keys(hass, entry, HOST)  # the entities of 1.2.x carry the address
    hass.config_entries.async_update_entry(
        entry,
        minor_version=1,
        unique_id=HOST,
        data={k: v for k, v in entry.data.items() if k not in (CONF_SERIAL, CONF_MAC)},
    )
    await hass.config_entries.async_unload(entry.entry_id)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: NEW_HOST, CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
    )
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.state is ConfigEntryState.LOADED
    assert _snapshot(hass, entry) == (entities, devices)
    ent_reg = er.async_get(hass)
    assert all(
        e.unique_id.startswith(f"{SERIAL}_")
        for e in er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    )


async def test_an_entry_that_was_left_half_migrated_is_healed(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    entities, devices = _snapshot(hass, entry)
    _to_old_keys(hass, entry, entry.entry_id)  # the entry says "done", the registries do not
    await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert _snapshot(hass, entry) == (entities, devices)
    (device,) = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert device.identifiers == {(DOMAIN, SERIAL)}


async def test_an_entity_created_twice_by_a_downgrade_leaves_one(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    ent_reg = er.async_get(hass)
    original = next(iter(er.async_entries_for_config_entry(ent_reg, entry.entry_id)))
    suffix = original.unique_id[len(f"{SERIAL}_") :]
    await hass.config_entries.async_unload(entry.entry_id)
    # 1.4.x ran in between: it created its own copy, bound to the entry id
    ent_reg.async_update_entity(original.entity_id, new_unique_id=f"{entry.entry_id}_{suffix}")
    ent_reg.async_get_or_create(
        original.domain, DOMAIN, f"{SERIAL}_{suffix}", config_entry=entry, suggested_object_id="x"
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    kept = ent_reg.async_get(original.entity_id)
    assert kept is not None
    assert kept.unique_id == f"{SERIAL}_{suffix}"
    same = [
        e
        for e in er.async_entries_for_config_entry(ent_reg, entry.entry_id)
        if e.unique_id == f"{SERIAL}_{suffix}"
    ]
    assert len(same) == 1


async def test_the_device_keeps_what_it_knows_when_the_modem_does_not_answer_at_setup(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    await hass.config_entries.async_unload(entry.entry_id)
    mock_client.async_get_device_info.side_effect = ZteH186ProtocolError("busy")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    (device,) = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert device.serial_number == SERIAL
    assert device.sw_version == "V1.0.0TY.1T2"


async def test_stopping_home_assistant_logs_off_from_the_modem(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    await _setup(hass, entry)
    mock_client.async_logout.reset_mock()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    mock_client.async_logout.assert_awaited()


async def test_the_older_of_two_copies_is_kept_after_a_downgrade(
    hass: HomeAssistant, mock_client
) -> None:
    """The entity of the serial number is the original; the copy of the older version goes."""
    entry = _modern()
    await _setup(hass, entry)
    ent_reg = er.async_get(hass)
    original = next(iter(er.async_entries_for_config_entry(ent_reg, entry.entry_id)))
    suffix = original.unique_id[len(f"{SERIAL}_") :]
    await hass.config_entries.async_unload(entry.entry_id)
    ent_reg.async_get_or_create(
        original.domain,
        DOMAIN,
        f"{entry.entry_id}_{suffix}",
        config_entry=entry,
        suggested_object_id="copy",
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert ent_reg.async_get(original.entity_id) is not None
    assert ent_reg.async_get(original.entity_id).unique_id == original.unique_id
    assert (
        ent_reg.async_get_entity_id(original.domain, DOMAIN, f"{entry.entry_id}_{suffix}") is None
    )


async def test_a_generated_title_of_an_older_form_is_brought_to_the_current_one(
    hass: HomeAssistant, mock_client
) -> None:
    entry = _modern()
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(entry, title=f"ZTE H186 {SERIAL}")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.title == TITLE
