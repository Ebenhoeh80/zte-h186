"""The ZTE H186 integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import ZteH186ApiClient
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from .coordinator import ZteH186ConfigEntry, ZteH186DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ZteH186ConfigEntry) -> bool:
    """Set up ZTE H186 from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data.get(CONF_USERNAME, "admin")
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
