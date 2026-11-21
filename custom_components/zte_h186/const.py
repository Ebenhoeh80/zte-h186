"""Constants for the ZTE H186 integration."""

from typing import Final

DOMAIN: Final = "zte_h186"
MANUFACTURER: Final = "ZTE"
MODEL: Final = "H186"

# Configuration keys
CONF_HOST: Final = "host"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_SCAN_INTERVAL: Final = "scan_interval"
# Option: log off from the modem after each update, so its single admin session is free.
CONF_RELEASE_SESSION: Final = "release_session"
# Identity of the physical modem, read from the modem itself (see docs/IDENTITY.md).
CONF_SERIAL: Final = "serial_number"
CONF_MAC: Final = "mac_address"
# Version 1.2 of an entry is identified by the modem's serial number (earlier: by its address).
CONFIG_ENTRY_MINOR_VERSION: Final = 2
TITLE_PREFIX: Final = "ZTE H186"

# Defaults
DEFAULT_USERNAME: Final = "admin"
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds
MIN_SCAN_INTERVAL: Final = 15  # seconds
MAX_SCAN_INTERVAL: Final = 600  # seconds
DEFAULT_RELEASE_SESSION: Final = False

# Normalized DSL line status (fixed enum option set for the status sensor).
# The raw modem value is kept verbatim in ZteH186Data.dsl_status; only the
# sensor presents it as one of these translated options.
DSL_STATUS_CONNECTED: Final = "connected"
DSL_STATUS_DISCONNECTED: Final = "disconnected"
DSL_STATUS_INITIALIZING: Final = "initializing"
DSL_STATUS_IDLE: Final = "idle"
DSL_STATUS_NO_SIGNAL: Final = "no_signal"
DSL_STATUS_DISABLED: Final = "disabled"

DSL_STATUS_OPTIONS: Final[list[str]] = [
    DSL_STATUS_CONNECTED,
    DSL_STATUS_DISCONNECTED,
    DSL_STATUS_INITIALIZING,
    DSL_STATUS_IDLE,
    DSL_STATUS_NO_SIGNAL,
    DSL_STATUS_DISABLED,
]

# The raw values of the modem's DSL answer that diagnostics may show (all are line metrics). Every
# other key of the answer is only listed by name, so nothing that identifies the modem or its
# owner can end up in a downloaded diagnostics file.
DSL_RAW_KEYS: Final[tuple[str, ...]] = (
    "Status",
    "IF_ERRORSTR",
    "CurrentProfile",
    "Module_type",
    "Data_path",
    "tLinkEncapsulationUsed",
    "Showtime_start",
    "Downstream_current_rate",
    "Upstream_current_rate",
    "Downstream_max_rate",
    "Upstream_max_rate",
    "Downstream_noise_margin",
    "Upstream_noise_margin",
    "Downstream_attenuation",
    "Upstream_attenuation",
    "Downstream_power",
    "Upstream_power",
    "DownInterleavedepth",
    "UpInterleaveDepth",
    "DownInterleaveDelay",
    "UpInterleaveDelay",
    "DownstreamInp",
    "UpstreamInp",
    "DownCrc_errors",
    "UpCrc_errors",
    "Fec_errors",
    "Atuc_fec_errors",
)
