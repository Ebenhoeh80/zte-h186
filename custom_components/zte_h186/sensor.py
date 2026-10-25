"""Support for ZTE H186 sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    EntityCategory,
    UnitOfDataRate,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ZteH186Data
from .const import CONF_HOST, DOMAIN, MANUFACTURER, MODEL
from .coordinator import ZteH186ConfigEntry, ZteH186DataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class ZteH186SensorEntityDescription(SensorEntityDescription):
    """Describes a ZTE H186 sensor entity."""

    value_fn: Callable[[ZteH186Data], StateType]


SENSOR_DESCRIPTIONS: tuple[ZteH186SensorEntityDescription, ...] = (
    # --- Primary Throughput & Sync Rates ---
    ZteH186SensorEntityDescription(
        key="downstream_sync",
        translation_key="downstream_sync",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=1,
        value_fn=lambda data: data.downstream_sync,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_sync",
        translation_key="upstream_sync",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=1,
        value_fn=lambda data: data.upstream_sync,
    ),
    ZteH186SensorEntityDescription(
        key="downstream_max",
        translation_key="downstream_max",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=1,
        value_fn=lambda data: data.downstream_max,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_max",
        translation_key="upstream_max",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=1,
        value_fn=lambda data: data.upstream_max,
    ),
    ZteH186SensorEntityDescription(
        key="downstream_capacity_ratio",
        translation_key="downstream_capacity_ratio",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:gauge",
        value_fn=lambda data: round((data.downstream_sync / data.downstream_max) * 100, 1)
        if data.downstream_max and data.downstream_max > 0
        else None,
    ),
    # --- Line Noise & Attenuation ---
    ZteH186SensorEntityDescription(
        key="downstream_snr",
        translation_key="downstream_snr",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        suggested_display_precision=1,
        value_fn=lambda data: data.downstream_snr,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_snr",
        translation_key="upstream_snr",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        suggested_display_precision=1,
        value_fn=lambda data: data.upstream_snr,
    ),
    ZteH186SensorEntityDescription(
        key="downstream_attenuation",
        translation_key="downstream_attenuation",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        suggested_display_precision=1,
        value_fn=lambda data: data.downstream_attenuation,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_attenuation",
        translation_key="upstream_attenuation",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        suggested_display_precision=1,
        value_fn=lambda data: data.upstream_attenuation,
    ),
    ZteH186SensorEntityDescription(
        key="downstream_power",
        translation_key="downstream_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:transmission-tower",
        value_fn=lambda data: data.downstream_power,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_power",
        translation_key="upstream_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:transmission-tower",
        value_fn=lambda data: data.upstream_power,
    ),
    # --- Line Profile & Modulation ---
    ZteH186SensorEntityDescription(
        key="profile",
        translation_key="profile",
        icon="mdi:tag-outline",
        value_fn=lambda data: data.profile,
    ),
    ZteH186SensorEntityDescription(
        key="modulation",
        translation_key="modulation",
        icon="mdi:router-network",
        value_fn=lambda data: data.modulation,
    ),
    ZteH186SensorEntityDescription(
        key="dsl_status",
        translation_key="dsl_status",
        icon="mdi:check-network-outline",
        value_fn=lambda data: data.dsl_status,
    ),
    ZteH186SensorEntityDescription(
        key="data_path",
        translation_key="data_path",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:transit-connection-variant",
        value_fn=lambda data: data.data_path,
    ),
    ZteH186SensorEntityDescription(
        key="link_encapsulation",
        translation_key="link_encapsulation",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:layers-outline",
        value_fn=lambda data: data.link_encapsulation,
    ),
    # --- Uptime / Showtime ---
    ZteH186SensorEntityDescription(
        key="showtime",
        translation_key="showtime",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.showtime,
    ),
    # --- Latency & Framing Diagnostics ---
    ZteH186SensorEntityDescription(
        key="downstream_interleave_depth",
        translation_key="downstream_interleave_depth",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sort-numeric-variant",
        value_fn=lambda data: data.downstream_interleave_depth,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_interleave_depth",
        translation_key="upstream_interleave_depth",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sort-numeric-variant",
        value_fn=lambda data: data.upstream_interleave_depth,
    ),
    ZteH186SensorEntityDescription(
        key="downstream_interleave_delay",
        translation_key="downstream_interleave_delay",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.downstream_interleave_delay,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_interleave_delay",
        translation_key="upstream_interleave_delay",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.upstream_interleave_delay,
    ),
    ZteH186SensorEntityDescription(
        key="downstream_inp",
        translation_key="downstream_inp",
        native_unit_of_measurement="symbols",
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:shield-check-outline",
        value_fn=lambda data: data.downstream_inp,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_inp",
        translation_key="upstream_inp",
        native_unit_of_measurement="symbols",
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:shield-check-outline",
        value_fn=lambda data: data.upstream_inp,
    ),
    # --- Error Counters ---
    ZteH186SensorEntityDescription(
        key="downstream_crc",
        translation_key="downstream_crc",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-circle-outline",
        value_fn=lambda data: data.downstream_crc,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_crc",
        translation_key="upstream_crc",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-circle-outline",
        value_fn=lambda data: data.upstream_crc,
    ),
    ZteH186SensorEntityDescription(
        key="downstream_fec",
        translation_key="downstream_fec",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wrench-outline",
        value_fn=lambda data: data.downstream_fec,
    ),
    ZteH186SensorEntityDescription(
        key="upstream_fec",
        translation_key="upstream_fec",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wrench-outline",
        value_fn=lambda data: data.upstream_fec,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZteH186ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZTE H186 sensor entities based on a config entry."""
    coordinator = entry.runtime_data
    host = entry.data[CONF_HOST]

    async_add_entities(
        ZteH186Sensor(coordinator, description, host)
        for description in SENSOR_DESCRIPTIONS
    )


class ZteH186Sensor(CoordinatorEntity[ZteH186DataUpdateCoordinator], SensorEntity):
    """Representation of a ZTE H186 sensor."""

    entity_description: ZteH186SensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZteH186DataUpdateCoordinator,
        description: ZteH186SensorEntityDescription,
        host: str,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return all raw modem XML attributes on the primary status sensor."""
        if (
            self.entity_description.key == "dsl_status"
            and self.coordinator.data
            and self.coordinator.data.raw_values
        ):
            return dict(self.coordinator.data.raw_values)
        return None
