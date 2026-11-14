"""The ZTE H186 integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .api import ZteH186ApiClient
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DEFAULT_USERNAME, DOMAIN
from .coordinator import ZteH186ConfigEntry, ZteH186DataUpdateCoordinator

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
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def _async_migrate_host_to_entry_id(hass: HomeAssistant, entry: ZteH186ConfigEntry) -> None:
    """Migrate legacy host-based unique IDs and device identifiers to entry_id.

    Releases up to 1.2.x bound every entity and the device to the modem host/IP
    (e.g. ``192.168.10.2_downstream_sync``). This rebinds them to the config
    entry, so changing the host via the reconfigure flow no longer orphans the
    entities and breaks their history.
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
    legacy_device = dev_reg.async_get_device(identifiers={(DOMAIN, entry.data[CONF_HOST].lower())})
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


async def async_reload_entry(hass: HomeAssistant, entry: ZteH186ConfigEntry) -> None:
    """Reload config entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
