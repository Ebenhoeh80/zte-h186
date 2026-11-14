"""Diagnostics support for ZTE H186."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from .coordinator import ZteH186ConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME, CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ZteH186ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "data": asdict(coordinator.data) if coordinator.data else None,
        "last_update_success": coordinator.last_update_success,
        "last_exception": repr(coordinator.last_exception),
    }
