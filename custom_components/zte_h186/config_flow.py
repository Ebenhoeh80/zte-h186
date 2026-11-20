"""Config flow for ZTE H186 integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .api import (
    ZteH186ApiClient,
    ZteH186AuthError,
    ZteH186ConnectionError,
    ZteH186DeviceInfo,
    ZteH186Error,
)
from .const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    CONF_USERNAME,
    CONFIG_ENTRY_MINOR_VERSION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .identity import modem_title, same_host

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.10.2"): cv.string,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


class ZteH186ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ZTE H186."""

    VERSION = 1
    MINOR_VERSION = CONFIG_ENTRY_MINOR_VERSION

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovered_host: str | None = None

    async def _async_validate_input(
        self, user_input: Mapping[str, Any], *, release_entries: list[ConfigEntry] | None = None
    ) -> tuple[dict[str, str], ZteH186DeviceInfo | None]:
        """Connect to the modem and return the errors, and what the modem says about itself.

        The modem allows one admin session at a time. If the entry that is being changed is running,
        its session is logged out first; it logs in again by itself at the next poll.
        """
        errors: dict[str, str] = {}
        info: ZteH186DeviceInfo | None = None
        for running in release_entries or []:
            if running.state is ConfigEntryState.LOADED:
                await running.runtime_data.client.async_logout()

        client = ZteH186ApiClient(
            host=user_input[CONF_HOST],
            username=user_input.get(CONF_USERNAME, DEFAULT_USERNAME),
            password=user_input[CONF_PASSWORD],
        )

        try:
            await client.async_login()
            await client.async_get_dsl_stats()
            info = await client.async_get_device_info()
        except ZteH186AuthError:
            errors["base"] = "invalid_auth"
        except ZteH186ConnectionError:
            errors["base"] = "cannot_connect"
        except ZteH186Error as err:
            _LOGGER.warning("Unexpected error during ZTE H186 setup: %s", err)
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception during ZTE H186 validation")
            errors["base"] = "unknown"
        finally:
            await client.close()

        return errors, info

    def _entry_at_address(self, host: str) -> ConfigEntry | None:
        """Return the entry that manages the modem at this address, if there is one."""
        for entry in self._async_current_entries(include_ignore=False):
            if same_host(entry.data.get(CONF_HOST, ""), host):
                return entry
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            user_input[CONF_HOST] = host
            # An entry from an older version that is not identified by its serial number yet is
            # recognised by its address (no second entry, and no second login that competes for the
            # modem's single session). For an entry that knows its serial number the comparison of
            # the
            # serial numbers decides; its running session is released for the check.
            at_address = self._entry_at_address(host)
            if at_address is not None and not at_address.data.get(CONF_SERIAL):
                return self.async_abort(reason="already_configured")

            # Any running entry may be the modem that is entered (under another name); the modem
            # has one admin session, so all of them are released for the check.
            errors, info = await self._async_validate_input(
                user_input, release_entries=self._async_current_entries(include_ignore=False)
            )

            if not errors and info is not None:
                # The modem is identified by its serial number, never by the address it was found
                # at.
                await self.async_set_unique_id(info.serial_number, raise_on_progress=False)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                if any(
                    not known.data.get(CONF_SERIAL) and known.state is not ConfigEntryState.LOADED
                    for known in self._async_current_entries(include_ignore=False)
                ):
                    # An entry of an older version that cannot reach its modem (it may have a new
                    # address) has not read the serial number yet: adding the modem here would
                    # make a second entry for it. Reconfigure that entry instead; it adopts the
                    # serial number.
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(
                    title=modem_title(info.serial_number),
                    data={
                        CONF_HOST: host,
                        CONF_USERNAME: user_input.get(CONF_USERNAME, DEFAULT_USERNAME),
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_SERIAL: info.serial_number,
                        **({CONF_MAC: info.mac_address} if info.mac_address else {}),
                    },
                )
            if not errors:
                errors["base"] = "cannot_connect"

        suggested = dict(user_input or {})
        if self._discovered_host and CONF_HOST not in suggested:
            suggested[CONF_HOST] = self._discovered_host
        schema = self.add_suggested_values_to_schema(STEP_USER_DATA_SCHEMA, suggested)

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> ConfigFlowResult:
        """Handle a device whose hardware address matches (the modem asked for an address, or got a
        new one).

        A known modem (recognised by its stored hardware address) gets its new address saved.
        An unknown
        device is offered if its login page says it is an H186; the serial number is read after the
        login.
        """
        host = discovery_info.ip
        mac = dr.format_mac(discovery_info.macaddress)
        for entry in self._async_current_entries(include_ignore=False):
            if entry.data.get(CONF_MAC) == mac:
                if entry.data.get(CONF_HOST) != host:
                    self.hass.config_entries.async_update_entry(
                        entry, data={**entry.data, CONF_HOST: host}
                    )
                    self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="already_configured")
            if same_host(entry.data.get(CONF_HOST, ""), host):
                return self.async_abort(reason="already_configured")

        model = await ZteH186ApiClient.async_probe_model(host, async_get_clientsession(self.hass))
        if model is None or "H186" not in model.upper():
            return self.async_abort(reason="not_supported")

        self._discovered_host = host
        self.context["title_placeholders"] = {"name": f"ZTE H186 ({host})"}
        return await self.async_step_user()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of an existing entry (the address or the credentials)."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip()
            combined_input = {**entry.data, **user_input}
            errors, info = await self._async_validate_input(combined_input, release_entries=[entry])

            if not errors and info is not None:
                stored = entry.data.get(CONF_SERIAL)
                if stored and stored != info.serial_number:
                    # A different modem must not take over the entities of this one.
                    return self.async_abort(reason="wrong_device")
                other = self.hass.config_entries.async_entry_for_domain_unique_id(
                    DOMAIN, info.serial_number
                )
                if other is not None and other.entry_id != entry.entry_id:
                    return self.async_abort(reason="already_configured")
                if not stored:
                    # An entry of an older version keeps its old identity here: the registries
                    # still carry the old address, which the setup needs to find them. The setup
                    # that follows the reload reads the serial number and completes the migration.
                    return self.async_update_reload_and_abort(entry, data_updates=user_input)
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        **user_input,
                        **({CONF_MAC: info.mac_address} if info.mac_address else {}),
                    },
                )
            if not errors:
                errors["base"] = "cannot_connect"

        reconfigure_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST)): cv.string,
                vol.Required(
                    CONF_USERNAME,
                    default=entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
                ): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )

        schema = self.add_suggested_values_to_schema(reconfigure_schema, user_input or {})

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Handle re-authentication when the modem rejects the stored credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth by asking for the username and password again."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            errors, info = await self._async_validate_input({**reauth_entry.data, **user_input})
            if not errors and info is not None:
                stored = reauth_entry.data.get(CONF_SERIAL)
                if stored and stored != info.serial_number:
                    return self.async_abort(reason="wrong_device")
                return self.async_update_reload_and_abort(reauth_entry, data_updates=user_input)
            if not errors:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=reauth_entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
                    ): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }
            ),
            errors=errors,
            description_placeholders={"host": reauth_entry.data[CONF_HOST]},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Create the options flow."""
        return ZteH186OptionsFlowHandler()


class ZteH186OptionsFlowHandler(OptionsFlowWithReload):
    """Handle options for ZTE H186."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval,
                ): vol.All(
                    cv.positive_int,
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
