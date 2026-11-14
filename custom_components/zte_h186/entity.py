"""Base entity for the ZTE H186 integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import ZteH186DataUpdateCoordinator


class ZteH186Entity(CoordinatorEntity[ZteH186DataUpdateCoordinator]):
    """Base class for all ZTE H186 entities.

    Entities are bound to the config entry (``entry_id``), not to the modem host.
    This keeps unique IDs and the device identity stable when the host/IP changes
    via the reconfigure flow, so entity history is preserved.
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
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name="ZTE H186",
            configuration_url=coordinator.client.base_url,
        )
