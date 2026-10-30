# Aquascape Smart Control — Home Assistant Integration

Home Assistant custom integration for Aquascape Smart Control devices. It
supports the Smart Control Hub for color-changing lights and the WiFi Smart
Pump Receiver.

Aquascape doesn't publish an API. This integration uses a reverse-engineered
HTTPS interface to the Blynk-based backend at
`smartcontrol.aquascapeinc.com`. See [docs/API.md](docs/API.md) for the
full protocol spec — pin map, V3 format, captured presets, and what's
not available (local control, MQTT push).

[hub]: https://www.aquascapeinc.com/smart-control-hub

## Features

- **Light entity** — on/off, brightness, RGB color picker
- **Effects dropdown** — the 8 built-in animation presets (Red/Orange/Green,
  Rainbow, Blue/Purple, etc.) plus `Solid` (freeze on current color) and
  `White Mode` (dedicated white channel)
- **Custom palettes** via the `aquascape.set_palette` service — any number of
  colors, fade or strobe, configurable speed
- **Animation Mode select** — Fade / Strobe toggle that re-applies the current
  effect immediately
- **Animation Speed slider** (1–10000, matches the Aquascape app)
- **WiFi RSSI sensor** for diagnostics
- **Multi-device** — add as many hubs as you have, each with its own token
- **Pump receiver fan entity** — on/off plus ten speed steps, suitable for
  Home Assistant's HomeKit Bridge

## Install

### HACS (recommended)

1. In HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/rabidfurball/hass-aquascape` as type **Integration**
3. Install **Aquascape Smart Control**
4. Restart Home Assistant

### Manual

1. Copy `custom_components/aquascape/` into your HA config's
   `custom_components/` directory
2. Restart Home Assistant

## Configure

1. Get the device auth token from the
   [Aquascape web dashboard](https://smartcontrol.aquascapeinc.com). Developer
   accounts show it in *Device Info*. Consumer accounts may need to inspect the
   incoming `dashws` WebSocket response for that device.
2. **Settings → Devices & Services → Add Integration → Aquascape**
3. Enter a name (e.g. "Front Yard Fountain") and paste the token

To add another hub, repeat with the new device's token.

## Services

### `aquascape.set_palette`

Activate an arbitrary multi-color animation. Pass any palette (1+ colors).

```yaml
service: aquascape.set_palette
data:
  device_id: a1b2c3d4e5f67890
  palette:
    - [255, 0, 128]   # any RGB
    - [0, 200, 255]
    - [80, 255, 0]
  strobe: false
  speed: 3000
```

### `aquascape.set_white_mode`

Switch to the hub's dedicated white channel — purer than RGB(255,255,255).

### `aquascape.set_solid_color`

Set a solid RGB color via RGB channels.

## Notes

- Aquascape's protocol is **cloud-only**. The hub speaks outbound to
  `smartcontrol.aquascapeinc.com` and exposes nothing on your LAN. There's
  currently no local-control path without reflashing the firmware.
- Default poll interval is **60 s** (configurable in the integration's
  Options). The integration also forces a refresh ~600 ms after every write
  so the UI tracks user actions without waiting for the next poll.

## Hardware tested

| Model | Result |
|---|---|
| Smart Control Hub model 84074 (rev 11/24) — color-changing pond/fountain lights | ✅ Working |
| WiFi Smart Pump Receiver — power and speed 1–10 | 🧪 Initial support |

### HomeKit

The pump is represented as a Home Assistant `fan`, with power and percentage
speed. Add the `fan` domain (or the individual pump entity) to Home Assistant's
HomeKit Bridge. Apple Home then presents a power control and speed slider.

If you've tested another Aquascape Smart Control product, please open an issue
or PR.

## Acknowledgements

- The protocol was reverse-engineered by inspecting the unauthenticated
  Blynk HTTPS API exposed by `smartcontrol.aquascapeinc.com`. Aquascape are
  not affiliated with this project.
- Built with [Claude Code](https://claude.com/claude-code).

## License

MIT — see [LICENSE](LICENSE).
