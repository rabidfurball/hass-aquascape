"""DataUpdateCoordinator for Aquascape devices."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AquascapeAPIError, AquascapeClient, parse_v3
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_DEVICE_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_PUMP,
    DOMAIN,
    PIN_ANIMATION_SPEED,
    PIN_BRIGHTNESS,
    PIN_POWER,
    PIN_PUMP_SPEED,
    PIN_RSSI,
    PIN_V3,
    PUMP_SPEED_DEFAULT,
    PUMP_SPEED_MAX,
    PUMP_SPEED_MIN,
)

_LOGGER = logging.getLogger(__name__)


class AquascapeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the Aquascape REST endpoint and exposes parsed device state."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: AquascapeClient,
    ) -> None:
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Pull /getAll and shape it for the entities."""
        try:
            raw = await self.client.get_all()
        except AquascapeAPIError as err:
            raise UpdateFailed(str(err)) from err

        # Entries created before pump support are lighting hubs.
        device_type = self.entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_LIGHT)
        if device_type == DEVICE_TYPE_PUMP:
            try:
                speed = int(float(raw.get(PIN_PUMP_SPEED.lower(), PUMP_SPEED_DEFAULT)))
            except (TypeError, ValueError):
                speed = PUMP_SPEED_DEFAULT
            speed = max(PUMP_SPEED_MIN, min(PUMP_SPEED_MAX, speed))
            try:
                power = int(float(raw.get(PIN_POWER.lower(), 0))) == 1
            except (TypeError, ValueError):
                power = False
            return {
                "device_type": DEVICE_TYPE_PUMP,
                "power": power,
                "pump_speed": speed,
            }

        # Pin keys come back lowercase from this backend ('v1', 'v2', ...)
        v3_str = raw.get(PIN_V3.lower(), "")
        v3 = parse_v3(v3_str) if v3_str else {
            "rgb": (0, 0, 0),
            "rgb_mode": False,
            "strobe": None,
            "palette": [],
        }

        return {
            "device_type": DEVICE_TYPE_LIGHT,
            "power": int(raw.get(PIN_POWER.lower(), 0)) == 1,
            "brightness": int(raw.get(PIN_BRIGHTNESS.lower(), 0)),
            "v3_raw": v3_str,
            "rgb": v3["rgb"],
            "rgb_mode": v3["rgb_mode"],
            "strobe": v3["strobe"],
            "palette": v3["palette"],
            "animation_speed": int(raw.get(PIN_ANIMATION_SPEED.lower(), 0)),
            "rssi": float(raw.get(PIN_RSSI.lower(), -100)),
        }

    async def async_request_refresh_soon(self, delay: float = 0.6) -> None:
        """Schedule a refresh shortly after a write so the UI catches up.

        We give the cloud a moment to reflect the write before polling.
        """
        from homeassistant.helpers.event import async_call_later

        async def _refresh(_now: Any) -> None:
            await self.async_request_refresh()

        async_call_later(self.hass, delay, _refresh)
