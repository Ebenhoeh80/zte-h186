"""Support for ZTE H186 buttons."""

from __future__ import annotations

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, DOMAIN, MANUFACTURER, MODEL
from .coordinator import ZteH186ConfigEntry, ZteH186DataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZteH186ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZTE H186 buttons."""
    coordinator = entry.runtime_data
    host = entry.data[CONF_HOST]

    async_add_entities([ZteH186RefreshButton(coordinator, host)])


class ZteH186RefreshButton(
    CoordinatorEntity[ZteH186DataUpdateCoordinator], ButtonEntity
):
    """Button to manually poll the ZTE H186 modem immediately."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh_stats"
    _attr_device_class = ButtonDeviceClass.UPDATE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: ZteH186DataUpdateCoordinator, host: str
    ) -> None:
        """Initialize button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{host.lower()}_refresh_stats"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host.lower())},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=f"ZTE H186 ({host})",
            configuration_url=f"http://{host}",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()
