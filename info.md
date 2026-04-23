# Aquascape Smart Control

Home Assistant custom integration for the Aquascape Smart Control Hub —
the WiFi controller that ships with Aquascape's color-changing pond and
fountain lights.

## Features

- **Light entity**: on/off, brightness, RGB color, dedicated white-channel mode
- **Effects dropdown** with the 8 built-in palette presets plus "Solid"
- **Custom palettes** via the `aquascape.set_palette` service — any number of colors, fade or strobe
- **Per-device select** for Fade vs Strobe animation mode
- **Per-device number** for animation speed (1–10000, matching the app's slider)
- **WiFi RSSI sensor** for diagnostics
- **Multi-device**: add as many hubs as you have, each with its own auth token

## Setup

1. Install via HACS (custom repository) or copy `custom_components/aquascape/` into your config
2. Get your hub's auth token from the Aquascape web dashboard at
   [smartcontrol.aquascapeinc.com](https://smartcontrol.aquascapeinc.com) →
   *Device → Device Info*
3. Settings → Devices & Services → **Add Integration** → search "Aquascape" →
   paste token + name
