"""Diagnostics support for ZTE H186."""

from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from homeassistant.components.diagnostics import REDACTED, async_redact_data
from homeassistant.core import HomeAssistant

from .const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SERIAL,
    CONF_USERNAME,
    DSL_RAW_KEYS,
)
from .coordinator import ZteH186ConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME, CONF_HOST, CONF_SERIAL, CONF_MAC, "unique_id", "title"}

_IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_MAC = re.compile(r"\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b")
_URL = re.compile(r"https?://\S+")


def _redact_text(text: str, secrets: set[str]) -> str:
    """Remove addresses, URLs, hardware addresses and the known identifiers from a message."""
    for secret in sorted((s for s in secrets if s), key=len, reverse=True):
        text = re.sub(re.escape(secret), REDACTED, text, flags=re.IGNORECASE)
    text = _URL.sub(REDACTED, text)
    text = _MAC.sub(REDACTED, text)
    return _IPV4.sub(REDACTED, text)


def _describe_exception(err: BaseException | None, secrets: set[str]) -> str | None:
    """Return the class name and the redacted message of an exception (never its repr)."""
    if err is None:
        return None
    message = _redact_text(str(err), secrets)
    return f"{type(err).__name__}: {message}" if message else type(err).__name__


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ZteH186ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    The modem's raw answer is reduced to a list of the known DSL values; everything else it sent is
    only listed by name, so no identifier that the modem happens to include can leak.
    """
    coordinator = entry.runtime_data
    secrets = {
        str(value) for key in (CONF_HOST, CONF_SERIAL, CONF_MAC) if (value := entry.data.get(key))
    }
    secrets.add(entry.title)
    if entry.unique_id:
        secrets.add(entry.unique_id)
    secrets.add(coordinator.client.base_url)

    data: dict[str, Any] | None = None
    if coordinator.data is not None:
        data = asdict(coordinator.data)
        raw = data.pop("raw_values", None) or {}
        data["raw_values"] = {key: raw[key] for key in DSL_RAW_KEYS if key in raw}
        data["raw_other_keys"] = sorted(key for key in raw if key not in DSL_RAW_KEYS)

    info = coordinator.device_info
    device: dict[str, Any] | None = None
    if info is not None:
        device = async_redact_data(
            {
                "serial_number": info.serial_number,
                "mac_address": info.mac_address,
                "model": info.model,
                "hardware_version": info.hardware_version,
                "software_version": info.software_version,
                "boot_version": info.boot_version,
                "dsl_version": info.dsl_version,
            },
            {"serial_number", "mac_address"},
        )

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "device": device,
        "data": data,
        "last_update_success": coordinator.last_update_success,
        "last_exception": _describe_exception(coordinator.last_exception, secrets),
    }
