"""Diagnostics support for ZTE H186."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD
from .coordinator import ZteH186ConfigEntry

TO_REDACT = {CONF_PASSWORD}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ZteH186ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    raw_data: dict[str, Any] = {}
    if coordinator.data is not None:
        raw_data = {
            "downstream_sync": coordinator.data.downstream_sync,
            "upstream_sync": coordinator.data.upstream_sync,
            "downstream_max": coordinator.data.downstream_max,
            "upstream_max": coordinator.data.upstream_max,
            "downstream_snr": coordinator.data.downstream_snr,
            "upstream_snr": coordinator.data.upstream_snr,
            "downstream_attenuation": coordinator.data.downstream_attenuation,
            "upstream_attenuation": coordinator.data.upstream_attenuation,
            "profile": coordinator.data.profile,
            "modulation": coordinator.data.modulation,
            "dsl_status": coordinator.data.dsl_status,
            "downstream_power": coordinator.data.downstream_power,
            "upstream_power": coordinator.data.upstream_power,
            "data_path": coordinator.data.data_path,
            "downstream_interleave_depth": coordinator.data.downstream_interleave_depth,
            "upstream_interleave_depth": coordinator.data.upstream_interleave_depth,
            "downstream_interleave_delay": coordinator.data.downstream_interleave_delay,
            "upstream_interleave_delay": coordinator.data.upstream_interleave_delay,
            "downstream_inp": coordinator.data.downstream_inp,
            "upstream_inp": coordinator.data.upstream_inp,
            "showtime": coordinator.data.showtime,
            "link_encapsulation": coordinator.data.link_encapsulation,
            "downstream_crc": coordinator.data.downstream_crc,
            "upstream_crc": coordinator.data.upstream_crc,
            "downstream_fec": coordinator.data.downstream_fec,
            "upstream_fec": coordinator.data.upstream_fec,
            "raw_xml_keys": list(coordinator.data.raw_values.keys())
            if coordinator.data.raw_values
            else [],
        }

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "coordinator_data": raw_data,
        "last_update_success": coordinator.last_update_success,
    }
