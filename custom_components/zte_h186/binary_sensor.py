"""Support for ZTE H186 binary sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ZteH186Data
from .const import CONF_HOST, DOMAIN, MANUFACTURER, MODEL
from .coordinator import ZteH186ConfigEntry, ZteH186DataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class ZteH186BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a ZTE H186 binary sensor entity."""

    is_on_fn: Callable[[ZteH186Data], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[ZteH186BinarySensorEntityDescription, ...] = (
    ZteH186BinarySensorEntityDescription(
        key="dsl_link",
        translation_key="dsl_link",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data: bool(
            data.dsl_status
            and data.dsl_status.lower() in ("up", "connected", "showtime")
            and data.downstream_sync > 0
        ),
    ),
    ZteH186BinarySensorEntityDescription(
        key="line_noise_warning",
        translation_key="line_noise_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: bool(
            data.downstream_snr < 6.0 or data.upstream_snr < 6.0
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZteH186ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZTE H186 binary sensors."""
    coordinator = entry.runtime_data
    host = entry.data[CONF_HOST]

    async_add_entities(
        ZteH186BinarySensor(coordinator, description, host)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class ZteH186BinarySensor(
    CoordinatorEntity[ZteH186DataUpdateCoordinator], BinarySensorEntity
):
    """Representation of a ZTE H186 binary sensor."""

    entity_description: ZteH186BinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZteH186DataUpdateCoordinator,
        description: ZteH186BinarySensorEntityDescription,
        host: str,
    ) -> None:
        """Initialize binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{host.lower()}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host.lower())},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=f"ZTE H186 ({host})",
            configuration_url=f"http://{host}",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data)
