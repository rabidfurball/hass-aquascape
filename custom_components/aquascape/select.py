"""Animation mode (Fade / Strobe) select for an Aquascape hub."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AquascapeAPIError, build_animation_v3
from .const import (
    CONF_NAME,
    DOMAIN,
    MANUFACTURER,
    MODE_FADE,
    MODE_OPTIONS,
    MODE_STROBE,
    MODEL,
    PIN_V3,
    PRESETS,
)
from .coordinator import AquascapeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AquascapeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AquascapeAnimationModeSelect(coordinator)])


class AquascapeAnimationModeSelect(
    CoordinatorEntity[AquascapeCoordinator], SelectEntity, RestoreEntity
):
    """User-facing Fade/Strobe toggle.

    The Aquascape protocol writes strobe-or-fade as part of the V3 animation
    string, so this select mostly exists to remember the user's preference
    across writes. When toggled, we re-apply the current effect with the
    new mode so the change takes effect immediately.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = MODE_OPTIONS
    _attr_has_entity_name = True
    _attr_translation_key = "animation_mode"
    _attr_icon = "mdi:pulse"

    def __init__(self, coordinator: AquascapeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_animation_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.data[CONF_NAME],
            manufacturer=MANUFACTURER,
            model=MODEL,
        )
        # Track the user's chosen mode locally; default to whatever the
        # device currently reports, falling back to Fade.
        device_strobe = self.coordinator.data.get("strobe")
        self._current = MODE_STROBE if device_strobe else MODE_FADE
        self._publish_helper_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in MODE_OPTIONS:
            self._current = last.state
            self._publish_helper_state()

    @property
    def current_option(self) -> str | None:
        return self._current

    async def async_select_option(self, option: str) -> None:
        if option not in MODE_OPTIONS:
            return
        previous = self._current
        self._current = option
        self._publish_helper_state()
        self.async_write_ha_state()

        if previous == option:
            return

        # Re-apply current effect (if any animation preset is active).
        palette = self.coordinator.data.get("palette") or []
        if not palette:
            return  # nothing to re-apply for solid / white modes

        # Match palette → known effect; if unknown, leave it alone.
        matched_palette = None
        for preset in PRESETS.values():
            if palette == preset:
                matched_palette = preset
                break
        if matched_palette is None:
            return

        v3 = build_animation_v3(matched_palette, strobe=(option == MODE_STROBE))
        try:
            await self.coordinator.client.write_pin(PIN_V3, v3)
        except AquascapeAPIError:
            return
        await self.coordinator.async_request_refresh_soon()

    def _publish_helper_state(self) -> None:
        """Stash this select's value where light.py can read it."""
        store = self.hass.data.setdefault(DOMAIN, {}).setdefault(
            f"{self.coordinator.entry.entry_id}_helpers", {}
        )
        store["strobe"] = self._current == MODE_STROBE
