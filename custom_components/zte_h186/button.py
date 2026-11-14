"""Support for ZTE H186 buttons."""

from __future__ import annotations

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ZteH186ConfigEntry
from .entity import ZteH186Entity

PARALLEL_UPDATES = 1

REFRESH_BUTTON = ButtonEntityDescription(
    key="refresh_stats",
    translation_key="refresh_stats",
    device_class=ButtonDeviceClass.UPDATE,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZteH186ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up ZTE H186 buttons."""
    coordinator = entry.runtime_data
    async_add_entities([ZteH186RefreshButton(coordinator, REFRESH_BUTTON)])


class ZteH186RefreshButton(ZteH186Entity, ButtonEntity):
    """Button to manually poll the ZTE H186 modem immediately."""

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()
