# Aquascape Smart Control — Home Assistant Integration

Home Assistant custom integration for the [Aquascape Smart Control Hub][hub]
— the WiFi controller that ships with Aquascape's color-changing pond and
fountain lights (model 84074).

Aquascape doesn't publish an API. This integration uses a reverse-engineered
HTTPS interface to the Blynk-based backend at
`smartcontrol.aquascapeinc.com`.

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

1. Get your hub's auth token from the
   [Aquascape web dashboard](https://smartcontrol.aquascapeinc.com) —
   *Device → Device Info*
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

If you've tested another Aquascape Smart Control product (Pump Receiver,
Smart Plug), please open an issue or PR.

## Acknowledgements

- The protocol was reverse-engineered by inspecting the unauthenticated
  Blynk HTTPS API exposed by `smartcontrol.aquascapeinc.com`. Aquascape are
  not affiliated with this project.
- Built with [Claude Code](https://claude.com/claude-code).

## License

MIT — see [LICENSE](LICENSE).
