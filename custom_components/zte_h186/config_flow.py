"""Config flow for ZTE H186 integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .api import (
    ZteH186ApiClient,
    ZteH186AuthError,
    ZteH186ConnectionError,
    ZteH186Error,
)
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.1.1"): cv.string,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


class ZteH186ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ZTE H186."""

    VERSION = 1

    async def _async_validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate the user input by connecting to the modem."""
        errors: dict[str, str] = {}
        client = ZteH186ApiClient(
            host=user_input[CONF_HOST],
            username=user_input.get(CONF_USERNAME, DEFAULT_USERNAME),
            password=user_input[CONF_PASSWORD],
        )

        try:
            await client.async_login()
            await client.async_get_dsl_stats()
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

        return errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()

            errors = await self._async_validate_input(user_input)

            if not errors:
                return self.async_create_entry(
                    title=f"ZTE H186 ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_USERNAME: user_input.get(CONF_USERNAME, DEFAULT_USERNAME),
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        schema = self.add_suggested_values_to_schema(
            STEP_USER_DATA_SCHEMA, user_input or {}
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of an existing entry."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            combined_input = {**entry.data, **user_input}
            errors = await self._async_validate_input(combined_input)

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )

        reconfigure_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST)): cv.string,
                vol.Required(
                    CONF_USERNAME, default=entry.data.get(CONF_USERNAME, DEFAULT_USERNAME)
                ): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )

        schema = self.add_suggested_values_to_schema(
            reconfigure_schema, user_input or {}
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return ZteH186OptionsFlowHandler()


class ZteH186OptionsFlowHandler(OptionsFlow):
    """Handle options for ZTE H186."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
