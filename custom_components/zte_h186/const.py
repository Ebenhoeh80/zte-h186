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
CONF_VERIFY_SSL: Final = "verify_ssl"

# Defaults
DEFAULT_USERNAME: Final = "admin"
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds
MIN_SCAN_INTERVAL: Final = 15  # seconds
MAX_SCAN_INTERVAL: Final = 600  # seconds
DEFAULT_TIMEOUT: Final = 15  # seconds
