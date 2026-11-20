"""Base entity for the ZTE H186 integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL, DOMAIN, MANUFACTURER, MODEL
from .coordinator import ZteH186DataUpdateCoordinator
from .identity import identity_key


class ZteH186Entity(CoordinatorEntity[ZteH186DataUpdateCoordinator]):
    """Base class for all ZTE H186 entities.

    Entities are bound to the modem's serial number, not to its address or to the config
    entry. This keeps unique IDs and the device identity stable when the host/IP changes and
    when the integration is removed and added again (see docs/IDENTITY.md). Until the serial
    number is known the config entry's id stands in for it.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZteH186DataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity and attach it to the config entry's device."""
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        key = identity_key(entry.entry_id, entry.data)
        self._attr_unique_id = f"{key}_{description.key}"
        info = coordinator.device_info
        device_info = DeviceInfo(
            identifiers={(DOMAIN, key)},
            manufacturer=MANUFACTURER,
            model=(info.model if info else None) or MODEL,
            name="ZTE H186",
            configuration_url=coordinator.client.base_url,
        )
        # What is not known right now (the modem did not answer at setup) is left out, so a value
        # that the registry has stays.
        if serial := entry.data.get(CONF_SERIAL):
            device_info["serial_number"] = serial
        if info and info.hardware_version:
            device_info["hw_version"] = info.hardware_version
        if info and info.software_version:
            device_info["sw_version"] = info.software_version
        self._attr_device_info = device_info
