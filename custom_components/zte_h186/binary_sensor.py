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
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import ZteH186Data
from .const import DSL_STATUS_CONNECTED
from .coordinator import ZteH186ConfigEntry
from .entity import ZteH186Entity
from .sensor import _normalize_dsl_status

PARALLEL_UPDATES = 0


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
            _normalize_dsl_status(data.dsl_status) == DSL_STATUS_CONNECTED
            and (data.downstream_sync or 0) > 0
        ),
    ),
    ZteH186BinarySensorEntityDescription(
        key="line_noise_warning",
        translation_key="line_noise_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: (
            None
            if data.downstream_snr is None or data.upstream_snr is None
            else data.downstream_snr < 6.0 or data.upstream_snr < 6.0
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZteH186ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up ZTE H186 binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        ZteH186BinarySensor(coordinator, description) for description in BINARY_SENSOR_DESCRIPTIONS
    )


class ZteH186BinarySensor(ZteH186Entity, BinarySensorEntity):
    """Representation of a ZTE H186 binary sensor."""

    entity_description: ZteH186BinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data)
