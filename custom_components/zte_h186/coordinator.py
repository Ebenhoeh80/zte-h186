"""DataUpdateCoordinator for the ZTE H186 integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ZteH186ApiClient,
    ZteH186AuthError,
    ZteH186ConnectionError,
    ZteH186Data,
    ZteH186Error,
)
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type ZteH186ConfigEntry = ConfigEntry[ZteH186DataUpdateCoordinator]


class ZteH186DataUpdateCoordinator(DataUpdateCoordinator[ZteH186Data]):
    """Class to manage fetching ZTE H186 data from the modem."""

    config_entry: ZteH186ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ZteH186ConfigEntry,
        client: ZteH186ApiClient,
    ) -> None:
        """Initialize coordinator."""
        self.client = client
        self.config_entry = config_entry

        scan_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL,
            config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.title})",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> ZteH186Data:
        """Fetch data from ZTE H186."""
        try:
            return await self.client.async_get_dsl_stats()
        except ZteH186AuthError as err:
            raise UpdateFailed(f"Authentication error with ZTE modem: {err}") from err
        except ZteH186ConnectionError as err:
            raise UpdateFailed(f"Connection error to ZTE modem: {err}") from err
        except ZteH186Error as err:
            raise UpdateFailed(f"Protocol error updating ZTE modem data: {err}") from err
