"""Constants for the Aquascape integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "aquascape"

# Configuration keys
CONF_TOKEN: Final = "token"
CONF_NAME: Final = "name"
CONF_BASE_URL: Final = "base_url"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_BASE_URL: Final = "https://smartcontrol.aquascapeinc.com"
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds

# Virtual pin names on the Blynk-based device
PIN_POWER: Final = "V1"
PIN_BRIGHTNESS: Final = "V2"
PIN_V3: Final = "V3"  # color/animation state
PIN_ANIMATION_SPEED: Final = "V8"
PIN_RSSI: Final = "V30"

# V3 string format: fields separated by null bytes
V3_DELIM: Final = "\x00"

# Built-in palette presets keyed by display name. Captured by stepping
# through the official Aquascape app and snapshotting V3 between each.
PRESETS: Final[dict[str, list[tuple[int, int, int]]]] = {
    "Red/Orange/Green": [(255, 0, 0), (255, 187, 0), (48, 255, 0)],
    "Dark Blue/Light Blue/Green": [(5, 44, 187), (0, 165, 238), (48, 255, 0)],
    "Blue/Purple": [(48, 35, 174), (200, 109, 215)],
    "Yellow/Orange": [(255, 202, 0), (255, 106, 0)],
    "Red/White/Blue": [(255, 0, 0), (255, 255, 255), (0, 0, 255)],
    "Red/Green/White": [(255, 0, 0), (48, 255, 0), (255, 255, 255)],
    "Magenta/Blue/Orange": [(255, 0, 255), (0, 0, 255), (255, 125, 0)],
    "Rainbow": [
        (255, 0, 0),
        (255, 255, 0),
        (0, 255, 0),
        (0, 255, 255),
        (0, 0, 255),
        (255, 0, 255),
    ],
}

# Effects shown in the light entity's effect_list, in order.
EFFECT_SOLID: Final = "Solid"
EFFECT_WHITE_MODE: Final = "White Mode"
EFFECT_LIST: Final = [EFFECT_SOLID, *PRESETS.keys(), EFFECT_WHITE_MODE]

# Animation speed range (matches the Aquascape app's slider)
SPEED_MIN: Final = 1
SPEED_MAX: Final = 10000
SPEED_DEFAULT: Final = 5000
SPEED_STEP: Final = 100

# Animation mode select
MODE_FADE: Final = "Fade"
MODE_STROBE: Final = "Strobe"
MODE_OPTIONS: Final = [MODE_FADE, MODE_STROBE]

MANUFACTURER: Final = "Aquascape"
MODEL: Final = "Smart Control Hub"
