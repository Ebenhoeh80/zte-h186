"""The ZTE H186 integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
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
    try:
        await coordinator.async_config_entry_first_refresh()
        await _async_ensure_identity(hass, entry, coordinator)
    except BaseException:
        # A failed setup must not leave the modem's single admin session occupied.
        await client.close()
        raise

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
    try:
        info = await coordinator.client.async_get_device_info()
    except ZteH186Error as err:
        if entry.data.get(CONF_SERIAL):
            _LOGGER.debug(
                "Could not read the device information (%s); using the stored serial number", err
            )
        else:
            _LOGGER.warning(
                "Could not read the modem's serial number (%s); "
                "the entry keeps its old identity until the next setup",
                err,
            )
        return
    coordinator.device_info = info
    serial = info.serial_number

    stored = entry.data.get(CONF_SERIAL)
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

    if (
        entry.minor_version < CONFIG_ENTRY_MINOR_VERSION
        or entry.unique_id != serial
        or stored != serial
        or entry.data.get(CONF_MAC) != info.mac_address
    ):
        await _async_apply_identity(hass, entry, serial, info.mac_address)


async def _async_apply_identity(
    hass: HomeAssistant, entry: ZteH186ConfigEntry, serial: str, mac: str | None
) -> None:
    """Make the serial number the identity of the entry, of its device and of its entities.

    The title is only replaced if the integration generated it; a name the user chose stays.
    Entities
    keep their entity ids (only the unique id changes), so history, areas and customisations stay.
    """
    old_key = entry.data.get(CONF_SERIAL) or entry.entry_id
    hass.config_entries.async_update_entry(
        entry,
        unique_id=serial,
        title=modem_title(serial) if is_generated_title(entry.title) else entry.title,
        data={**entry.data, CONF_SERIAL: serial, **({CONF_MAC: mac} if mac else {})},
        minor_version=CONFIG_ENTRY_MINOR_VERSION,
    )
    await _async_migrate_registries(hass, entry, old_key, serial)


async def _async_migrate_registries(
    hass: HomeAssistant, entry: ZteH186ConfigEntry, old_key: str, serial: str
) -> None:
    """Rebind the entities' unique ids and the device identifier from the old key to the serial
    number."""
    if old_key == serial:
        return
    old_prefix = f"{old_key}_"

    @callback
    def _migrate_entity(entity_entry: er.RegistryEntry) -> dict[str, str] | None:
        if entity_entry.unique_id.startswith(old_prefix):
            return {"new_unique_id": f"{serial}_{entity_entry.unique_id[len(old_prefix) :]}"}
        return None

    try:
        await er.async_migrate_entries(hass, entry.entry_id, _migrate_entity)
    except ValueError as err:  # a unique id of the new form exists already
        _LOGGER.error("Could not move the entities to the serial number: %s", err)

    dev_reg = dr.async_get(hass)
    device = _async_get_entry_device(dev_reg, entry, (DOMAIN, old_key))
    if device is not None and (DOMAIN, serial) not in device.identifiers:
        dev_reg.async_update_device(device.id, new_identifiers={(DOMAIN, serial)})


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
