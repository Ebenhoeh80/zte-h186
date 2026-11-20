"""The ZTE H186 integration."""

from __future__ import annotations

import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .api import ZteH186ApiClient, ZteH186Error
from .const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SERIAL,
    CONF_USERNAME,
    CONFIG_ENTRY_MINOR_VERSION,
    DEFAULT_USERNAME,
    DOMAIN,
)
from .coordinator import ZteH186ConfigEntry, ZteH186DataUpdateCoordinator
from .identity import is_generated_title, modem_title

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ZteH186ConfigEntry) -> bool:
    """Set up ZTE H186 from a config entry."""
    await _async_migrate_host_to_entry_id(hass, entry)

    host = entry.data[CONF_HOST]
    username = entry.data.get(CONF_USERNAME, DEFAULT_USERNAME)
    password = entry.data[CONF_PASSWORD]

    client = ZteH186ApiClient(
        host=host,
        username=username,
        password=password,
    )

    coordinator = ZteH186DataUpdateCoordinator(hass, entry, client)

    async def _async_log_off(_event: Event | None = None) -> None:
        await client.async_logout()

    try:
        await coordinator.async_config_entry_first_refresh()
        await _async_ensure_identity(hass, entry, coordinator)
        entry.runtime_data = coordinator
        # Home Assistant stopping does not unload the entries; without this the modem's single
        # admin session stays occupied for minutes and the next start is refused.
        entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_log_off))
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        # A failed setup must not leave the modem's single admin session occupied.
        await client.close()
        raise

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ZteH186ConfigEntry) -> bool:
    """Accept entries of version 1.

    Moving an entry to the serial number as its identity needs the modem (it reports the serial
    number), so it happens at the next setup, when the modem answers (see
    ``_async_ensure_identity``).
    """
    return entry.version <= 1


async def _async_ensure_identity(
    hass: HomeAssistant, entry: ZteH186ConfigEntry, coordinator: ZteH186DataUpdateCoordinator
) -> None:
    """Identify the modem by its serial number: check it is the modem of this entry and migrate
    older entries.

    A modem that cannot report its serial number right now (for example a busy web interface)
    leaves an older entry as it is; it is migrated at the next setup that succeeds.
    """
    stored = entry.data.get(CONF_SERIAL)
    try:
        info = await coordinator.client.async_get_device_info()
    except ZteH186Error as err:
        if stored:
            _LOGGER.debug(
                "Could not read the device information (%s); using the stored serial number", err
            )
            _async_migrate_registries(hass, entry, stored)
        else:
            _LOGGER.warning(
                "Could not read the modem's serial number (%s); "
                "the entry keeps its old identity until the next setup",
                err,
            )
        return
    coordinator.device_info = info
    serial = info.serial_number

    if stored and stored != serial:
        # Another modem answers at the saved address: its entities must not be mixed into this
        # entry.
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="wrong_modem",
            translation_placeholders={"expected": "…" + stored[-4:], "found": "…" + serial[-4:]},
        )
    owner = hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, serial)
    if owner is not None and owner.entry_id != entry.entry_id:
        # One modem, two entries would create every device twice. Only the first one runs.
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="duplicate_modem",
            translation_placeholders={"title": owner.title},
        )

    # The registries first, the entry last: the migration does not depend on what the entry stores
    # (so it also heals an entry that a reconfigure, an interrupted setup or a downgrade left
    # half-way) and can be repeated at every setup.
    _async_migrate_registries(hass, entry, serial)
    if (
        entry.minor_version < CONFIG_ENTRY_MINOR_VERSION
        or entry.unique_id != serial
        or stored != serial
        or entry.data.get(CONF_MAC) != info.mac_address
        # a title the integration generated in an older form is brought to the current one
        or (is_generated_title(entry.title) and entry.title != modem_title(serial))
    ):
        hass.config_entries.async_update_entry(
            entry,
            unique_id=serial,
            # Only a title the integration generated is replaced; a name the user chose stays.
            title=modem_title(serial) if is_generated_title(entry.title) else entry.title,
            data={
                **entry.data,
                CONF_SERIAL: serial,
                **({CONF_MAC: info.mac_address} if info.mac_address else {}),
            },
            minor_version=CONFIG_ENTRY_MINOR_VERSION,
        )


@callback
def _async_migrate_registries(hass: HomeAssistant, entry: ZteH186ConfigEntry, serial: str) -> None:
    """Rebind the entities' unique ids and the device identifier to the serial number.

    Everything an older version bound to the config entry id, to the address or to the address in
    the unique id of the entry is moved; entity ids, areas, names and history stay (only the unique
    id changes). Nothing happens when everything is bound to the serial number already.
    """
    old_keys = {entry.entry_id, entry.data.get(CONF_HOST, "").lower()}
    if entry.unique_id and entry.unique_id != serial:
        old_keys.add(entry.unique_id.lower())
    old_keys.discard("")
    old_keys.discard(serial.lower())

    ent_reg = er.async_get(hass)
    new_prefix = f"{serial}_"
    for entity_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if entity_entry.unique_id.startswith(new_prefix):
            continue
        for key in old_keys:
            old_prefix = f"{key}_"
            if not entity_entry.unique_id.startswith(old_prefix):
                continue
            new_unique_id = f"{new_prefix}{entity_entry.unique_id[len(old_prefix) :]}"
            clash_id = ent_reg.async_get_entity_id(entity_entry.domain, DOMAIN, new_unique_id)
            if clash_id is not None:
                # A version that ran after a downgrade created a second copy next to the original.
                # The older one is the original: it carries the history and the customisations.
                clash = ent_reg.async_get(clash_id)
                if clash is not None and clash.created_at <= entity_entry.created_at:
                    ent_reg.async_remove(entity_entry.entity_id)
                    break
                ent_reg.async_remove(clash_id)
            ent_reg.async_update_entity(entity_entry.entity_id, new_unique_id=new_unique_id)
            break

    dev_reg = dr.async_get(hass)
    current = _async_get_entry_device(dev_reg, entry, (DOMAIN, serial))
    for key in old_keys:
        device = _async_get_entry_device(dev_reg, entry, (DOMAIN, key))
        if device is None or (current is not None and device.id == current.id):
            continue
        if current is None:
            dev_reg.async_update_device(device.id, new_identifiers={(DOMAIN, serial)})
            current = device
        else:
            # A duplicate that an older version created: its entities move to the device first (a
            # removed device takes its entities with it).
            for entity_entry in er.async_entries_for_device(
                ent_reg, device.id, include_disabled_entities=True
            ):
                ent_reg.async_update_entity(entity_entry.entity_id, device_id=current.id)
            dev_reg.async_remove_device(device.id)


def _async_get_entry_device(
    dev_reg: dr.DeviceRegistry, entry: ZteH186ConfigEntry, identifier: tuple[str, str]
) -> dr.DeviceEntry | None:
    """Return the device of this config entry that has the identifier, if any.

    Recent Home Assistant versions look devices up per config entry and deprecate
    the entry-agnostic ``async_get_device`` (identifiers are no longer unique across
    config entries). Older versions only have the latter, so fall back to it there.
    """
    lookup = getattr(dev_reg, "async_get_device_by_identifier", None)
    if lookup is not None:
        return lookup(identifier, entry.entry_id)
    return dev_reg.async_get_device(identifiers={identifier})


async def _async_migrate_host_to_entry_id(hass: HomeAssistant, entry: ZteH186ConfigEntry) -> None:
    """Migrate legacy host-based unique IDs and device identifiers to entry_id.

    Releases up to 1.2.x bound every entity and the device to the modem host/IP
    (e.g. ``192.168.10.2_downstream_sync``). This rebinds them to the config
    entry, so changing the host via the reconfigure flow no longer orphans the
    entities and breaks their history. (From 1.5.0 the serial number replaces the
    entry id, see ``_async_ensure_identity``.)
    """
    old_prefix = f"{entry.data[CONF_HOST].lower()}_"

    @callback
    def _migrate_entity(entity_entry: er.RegistryEntry) -> dict[str, str] | None:
        if entity_entry.unique_id.startswith(old_prefix):
            suffix = entity_entry.unique_id[len(old_prefix) :]
            return {"new_unique_id": f"{entry.entry_id}_{suffix}"}
        return None

    await er.async_migrate_entries(hass, entry.entry_id, _migrate_entity)

    dev_reg = dr.async_get(hass)
    legacy_device = _async_get_entry_device(dev_reg, entry, (DOMAIN, entry.data[CONF_HOST].lower()))
    if legacy_device is not None and (DOMAIN, entry.entry_id) not in legacy_device.identifiers:
        dev_reg.async_update_device(
            legacy_device.id,
            new_identifiers={(DOMAIN, entry.entry_id)},
        )


async def async_unload_entry(hass: HomeAssistant, entry: ZteH186ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = entry.runtime_data
        await coordinator.client.close()
    return unload_ok
