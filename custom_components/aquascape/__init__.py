"""The Aquascape Smart Control integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AquascapeAPIError,
    AquascapeClient,
    build_animation_v3,
    build_solid_v3,
    build_white_mode_v3,
)
from .const import (
    CONF_BASE_URL,
    CONF_TOKEN,
    DEFAULT_BASE_URL,
    DOMAIN,
    PIN_ANIMATION_SPEED,
    PIN_V3,
    SPEED_DEFAULT,
    SPEED_MAX,
    SPEED_MIN,
)
from .coordinator import AquascapeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

SERVICE_SET_PALETTE = "set_palette"
SERVICE_SET_WHITE_MODE = "set_white_mode"
SERVICE_SET_SOLID_COLOR = "set_solid_color"

PALETTE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("palette"): vol.All(
            cv.ensure_list,
            vol.Length(min=1),
            [vol.All(cv.ensure_list, vol.Length(min=3, max=3), [vol.Range(0, 255)])],
        ),
        vol.Optional("strobe", default=False): cv.boolean,
        vol.Optional("speed", default=SPEED_DEFAULT): vol.All(
            int, vol.Range(min=SPEED_MIN, max=SPEED_MAX)
        ),
    }
)

WHITE_MODE_SCHEMA = vol.Schema({vol.Required("device_id"): cv.string})

SOLID_COLOR_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("rgb_color"): vol.All(
            cv.ensure_list, vol.Length(min=3, max=3), [vol.Range(0, 255)]
        ),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an Aquascape hub from a config entry."""
    session = async_get_clientsession(hass)
    client = AquascapeClient(
        session,
        entry.data[CONF_TOKEN],
        base_url=entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
    )
    coordinator = AquascapeCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    _async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SET_PALETTE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_WHITE_MODE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_SOLID_COLOR)
    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change so scan_interval picks up."""
    await hass.config_entries.async_reload(entry.entry_id)


def _coordinator_for_device(
    hass: HomeAssistant, device_id: str
) -> AquascapeCoordinator:
    """Resolve a HA device_id back to its coordinator."""
    from homeassistant.helpers import device_registry as dr

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(device_id)
    if device is None:
        raise HomeAssistantError(f"Device {device_id} not found")
    for entry_id in device.config_entries:
        coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
        if coordinator is not None:
            return coordinator
    raise HomeAssistantError(f"No Aquascape device for {device_id}")


def _async_register_services(hass: HomeAssistant) -> None:
    """Register the integration's services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_PALETTE):
        return

    async def _set_palette(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data["device_id"])
        palette = [tuple(c) for c in call.data["palette"]]
        v3 = build_animation_v3(palette, strobe=call.data["strobe"])
        try:
            await coordinator.client.write_pin(PIN_V3, v3)
            await coordinator.client.write_pin(
                PIN_ANIMATION_SPEED, int(call.data["speed"])
            )
        except AquascapeAPIError as err:
            raise HomeAssistantError(str(err)) from err
        await coordinator.async_request_refresh_soon()

    async def _set_white_mode(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data["device_id"])
        try:
            await coordinator.client.write_pin(PIN_V3, build_white_mode_v3())
        except AquascapeAPIError as err:
            raise HomeAssistantError(str(err)) from err
        await coordinator.async_request_refresh_soon()

    async def _set_solid_color(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data["device_id"])
        r, g, b = call.data["rgb_color"]
        try:
            await coordinator.client.write_pin(PIN_V3, build_solid_v3(r, g, b))
        except AquascapeAPIError as err:
            raise HomeAssistantError(str(err)) from err
        await coordinator.async_request_refresh_soon()

    hass.services.async_register(DOMAIN, SERVICE_SET_PALETTE, _set_palette, schema=PALETTE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_SET_WHITE_MODE, _set_white_mode, schema=WHITE_MODE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_SOLID_COLOR, _set_solid_color, schema=SOLID_COLOR_SCHEMA
    )
