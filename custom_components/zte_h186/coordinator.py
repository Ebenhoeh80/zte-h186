"""DataUpdateCoordinator for the ZTE H186 integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ZteH186ApiClient,
    ZteH186AuthError,
    ZteH186ConnectionError,
    ZteH186Data,
    ZteH186DeviceInfo,
    ZteH186Error,
)
from .const import CONF_HOST, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# A running integration asks for credentials only after this many refused logins in a row.
AUTH_FAILURES_BEFORE_REAUTH = 2

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
        # What the modem reports about itself; read once per setup (``None`` while unknown).
        self.device_info: ZteH186DeviceInfo | None = None
        # Rejected logins in a row while running (see ``_async_update_data``).
        self._auth_failures = 0

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
        host = self.config_entry.data[CONF_HOST]
        try:
            async with asyncio.timeout(30):
                data = await self.client.async_get_dsl_stats()
        except ZteH186AuthError as err:
            self._auth_failures += 1
            if self.data is not None and self._auth_failures < AUTH_FAILURES_BEFORE_REAUTH:
                # The modem allows one admin session; a login that is refused while it works is
                # usually that session being busy (web interface open), not a changed password.
                # Retry at the next poll instead of asking the user for credentials.
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="auth_retry",
                    translation_placeholders={"host": host},
                ) from err
            # Triggers Home Assistant's reauth flow instead of retrying forever.
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
                translation_placeholders={"host": host},
            ) from err
        except TimeoutError as err:
            self._auth_failures = 0
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_timeout",
                translation_placeholders={"host": host},
            ) from err
        except ZteH186ConnectionError as err:
            self._auth_failures = 0
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"host": host},
            ) from err
        except ZteH186Error as err:
            self._auth_failures = 0
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="protocol_error",
                translation_placeholders={"error": str(err)},
            ) from err
        self._auth_failures = 0
        return data
