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
