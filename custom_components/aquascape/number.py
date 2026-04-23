"""Animation speed number entity."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AquascapeAPIError
from .const import (
    CONF_NAME,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    PIN_ANIMATION_SPEED,
    SPEED_DEFAULT,
    SPEED_MAX,
    SPEED_MIN,
    SPEED_STEP,
)
from .coordinator import AquascapeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AquascapeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AquascapeAnimationSpeedNumber(coordinator)])


class AquascapeAnimationSpeedNumber(
    CoordinatorEntity[AquascapeCoordinator], NumberEntity, RestoreEntity
):
    """Slider for the Aquascape app's animation-speed value (V8)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = SPEED_MIN
    _attr_native_max_value = SPEED_MAX
    _attr_native_step = SPEED_STEP
    _attr_mode = NumberMode.SLIDER
    _attr_has_entity_name = True
    _attr_translation_key = "animation_speed"
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: AquascapeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_animation_speed"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.data[CONF_NAME],
            manufacturer=MANUFACTURER,
            model=MODEL,
        )
        device_speed = coordinator.data.get("animation_speed") or SPEED_DEFAULT
        self._current = float(device_speed)
        self._publish_helper_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable", None):
            try:
                self._current = float(last.state)
            except (TypeError, ValueError):
                pass
        self._publish_helper_state()

    @property
    def native_value(self) -> float:
        return self._current

    async def async_set_native_value(self, value: float) -> None:
        self._current = max(SPEED_MIN, min(SPEED_MAX, value))
        self._publish_helper_state()
        self.async_write_ha_state()
        try:
            await self.coordinator.client.write_pin(
                PIN_ANIMATION_SPEED, int(self._current)
            )
        except AquascapeAPIError:
            return
        await self.coordinator.async_request_refresh_soon()

    def _publish_helper_state(self) -> None:
        store = self.hass.data.setdefault(DOMAIN, {}).setdefault(
            f"{self.coordinator.entry.entry_id}_helpers", {}
        )
        store["speed"] = int(self._current)
