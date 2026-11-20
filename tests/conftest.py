"""Shared fixtures for the ZTE H186 Home Assistant tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zte_h186.api import ZteH186Data, ZteH186DeviceInfo
from custom_components.zte_h186.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DOMAIN,
)

SERIAL = "ZTE0123456789A42"
MAC = "dc:f8:b9:00:11:22"


@pytest.fixture
def device_info() -> ZteH186DeviceInfo:
    """What the modem reports about itself (serial number and MAC address are made up)."""
    return ZteH186DeviceInfo(
        serial_number=SERIAL,
        mac_address=MAC,
        model="H186",
        hardware_version="V1.0.0",
        software_version="V1.0.0TY.1T2",
        boot_version="V1.0.0",
        dsl_version="8B1017_8B0701",
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading the ZTE H186 custom integration in every test."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry for the ZTE H186 integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="ZTE H186 (192.168.10.2)",
        unique_id="192.168.10.2",
        data={
            CONF_HOST: "192.168.10.2",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
        },
        options={CONF_SCAN_INTERVAL: 60},
    )


@pytest.fixture
def dsl_data_up() -> ZteH186Data:
    """Return normalized data for a line in Showtime (values from real hardware)."""
    return ZteH186Data(
        downstream_sync=116.798,
        upstream_sync=36.999,
        downstream_max=134.784,
        upstream_max=41.24,
        downstream_snr=10.3,
        upstream_snr=6.8,
        downstream_attenuation=11.0,
        upstream_attenuation=11.2,
        profile="17a",
        modulation="VDSL2_Vectoring",
        dsl_status="Up",
        downstream_power=14.4,
        upstream_power=0.0,
        data_path="Fast/Fast",
        downstream_interleave_depth=1,
        upstream_interleave_depth=1,
        downstream_interleave_delay=0,
        upstream_interleave_delay=0,
        downstream_inp=72.0,
        upstream_inp=45.0,
        showtime=2017149,
        link_encapsulation="G.993.2_Annex_K_PTM",
        downstream_crc=26,
        upstream_crc=0,
        downstream_fec=0,
        upstream_fec=364,
        raw_values={
            "Status": "Up",
            "CurrentProfile": "17a",
            "Module_type": "VDSL2_Vectoring",
            "Downstream_current_rate": "116798",
            "Upstream_current_rate": "36999",
        },
    )


@pytest.fixture
def dsl_data_down() -> ZteH186Data:
    """Return normalized data for a line that is down (metrics unknown)."""
    return ZteH186Data(
        downstream_sync=None,
        upstream_sync=None,
        downstream_max=None,
        upstream_max=None,
        downstream_snr=None,
        upstream_snr=None,
        downstream_attenuation=None,
        upstream_attenuation=None,
        profile=None,
        modulation=None,
        dsl_status="Down",
        raw_values={"Status": "Down"},
    )


@pytest.fixture
def mock_client(dsl_data_up: ZteH186Data, device_info: ZteH186DeviceInfo) -> Generator[AsyncMock]:
    """Patch ZteH186ApiClient so __init__ and config_flow use a mocked modem."""
    with (
        patch("custom_components.zte_h186.ZteH186ApiClient", autospec=True) as init_client,
        patch(
            "custom_components.zte_h186.config_flow.ZteH186ApiClient",
            new=init_client,
        ),
    ):
        client = init_client.return_value
        client.async_login = AsyncMock()
        client.async_get_dsl_stats = AsyncMock(return_value=dsl_data_up)
        client.async_get_device_info = AsyncMock(return_value=device_info)
        client.async_logout = AsyncMock()
        init_client.async_probe_model = AsyncMock(return_value="H186")
        client.close = AsyncMock()
        client.base_url = "http://192.168.10.2"
        yield client
