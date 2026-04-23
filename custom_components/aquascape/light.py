"""Light entity for an Aquascape hub."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import (
    AquascapeAPIError,
    build_animation_v3,
    build_solid_v3,
    build_white_mode_v3,
)
from .const import (
    CONF_NAME,
    DOMAIN,
    EFFECT_LIST,
    EFFECT_SOLID,
    EFFECT_WHITE_MODE,
    MANUFACTURER,
    MODE_STROBE,
    MODEL,
    PIN_ANIMATION_SPEED,
    PIN_BRIGHTNESS,
    PIN_POWER,
    PIN_V3,
    PRESETS,
    SPEED_DEFAULT,
)
from .coordinator import AquascapeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light entity for this hub."""
    coordinator: AquascapeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AquascapeLight(coordinator)])


def _palette_to_effect_name(palette: list[tuple[int, int, int]]) -> str:
    """Reverse-match a palette against the known presets."""
    for name, preset in PRESETS.items():
        if palette == preset:
            return name
    return "Custom"


class AquascapeLight(CoordinatorEntity[AquascapeCoordinator], LightEntity):
    """Light entity that wraps the V1/V2/V3 pins of an Aquascape hub."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = EFFECT_LIST
    _attr_has_entity_name = True
    _attr_name = None  # use the device name

    def __init__(self, coordinator: AquascapeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_light"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.data[CONF_NAME],
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("power"))

    @property
    def brightness(self) -> int | None:
        pct = self.coordinator.data.get("brightness", 0)
        return int(pct * 255 / 100)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        return self.coordinator.data.get("rgb")

    @property
    def effect(self) -> str | None:
        data = self.coordinator.data
        v3_raw = data.get("v3_raw", "")
        if not v3_raw:
            return None
        if not data.get("rgb_mode") and data.get("rgb") == (255, 255, 255):
            return EFFECT_WHITE_MODE
        palette = data.get("palette") or []
        if not palette:
            return EFFECT_SOLID
        return _palette_to_effect_name(palette)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Translate HA's combined turn_on call into pin writes."""
        client = self.coordinator.client

        # Effect-only call OR effect chosen alongside on/brightness.
        # When the user picks an effect, that should take precedence over
        # any color in the same call (HA UI doesn't usually send both,
        # but be defensive).
        try:
            if ATTR_EFFECT in kwargs:
                await self._apply_effect(kwargs[ATTR_EFFECT])
            elif ATTR_RGB_COLOR in kwargs:
                r, g, b = kwargs[ATTR_RGB_COLOR]
                await client.write_pin(PIN_V3, build_solid_v3(r, g, b))

            if ATTR_BRIGHTNESS in kwargs:
                pct = max(0, min(100, int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)))
                await client.write_pin(PIN_BRIGHTNESS, pct)

            # Always ensure power is on if we're handling turn_on
            if not self.is_on:
                await client.write_pin(PIN_POWER, 1)
        except AquascapeAPIError as err:
            from homeassistant.exceptions import HomeAssistantError

            raise HomeAssistantError(str(err)) from err

        await self.coordinator.async_request_refresh_soon()

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            await self.coordinator.client.write_pin(PIN_POWER, 0)
        except AquascapeAPIError as err:
            from homeassistant.exceptions import HomeAssistantError

            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh_soon()

    async def _apply_effect(self, effect: str) -> None:
        """Apply a named effect from EFFECT_LIST."""
        client = self.coordinator.client

        if effect == EFFECT_WHITE_MODE:
            await client.write_pin(PIN_V3, build_white_mode_v3())
            return

        if effect == EFFECT_SOLID:
            # Freeze on currently displayed color, drop animation
            r, g, b = self.coordinator.data.get("rgb", (255, 255, 255))
            await client.write_pin(PIN_V3, build_solid_v3(r, g, b))
            return

        palette = PRESETS.get(effect)
        if palette is None:
            return

        # Pull strobe + speed from the per-device select/number entities.
        # Their states are exposed through helper functions on the
        # coordinator so we don't reach into hass.states from here.
        strobe = self.coordinator.entry.options.get("strobe_mode") == MODE_STROBE
        speed = self.coordinator.entry.options.get("animation_speed", SPEED_DEFAULT)

        # Look up the live values from the helper entities the user toggles.
        # These are stored in hass.data alongside the coordinator.
        hass = self.coordinator.hass
        store = hass.data.get(DOMAIN, {}).get(
            f"{self.coordinator.entry.entry_id}_helpers", {}
        )
        if store:
            strobe = store.get("strobe", strobe)
            speed = store.get("speed", speed)

        await client.write_pin(PIN_V3, build_animation_v3(palette, strobe=strobe))
        await client.write_pin(PIN_ANIMATION_SPEED, int(speed))
