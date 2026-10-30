"""Fan entity for an Aquascape Smart Pump Receiver."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AquascapeAPIError
from .const import (
    CONF_DEVICE_TYPE,
    CONF_NAME,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_PUMP,
    DOMAIN,
    MANUFACTURER,
    PIN_POWER,
    PIN_PUMP_SPEED,
    PUMP_MODEL,
    PUMP_SPEED_MIN,
    pump_percentage_to_speed,
    pump_speed_to_percentage,
)
from .coordinator import AquascapeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a fan entity only for a detected pump receiver."""
    if entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_LIGHT) != DEVICE_TYPE_PUMP:
        return
    coordinator: AquascapeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AquascapePumpFan(coordinator)])


class AquascapePumpFan(CoordinatorEntity[AquascapeCoordinator], FanEntity):
    """Expose pump power and speed in HA and HomeKit."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:water-pump"
    _attr_speed_count = 10
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: AquascapeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_pump"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.data[CONF_NAME],
            manufacturer=MANUFACTURER,
            model=PUMP_MODEL,
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("power"))

    @property
    def percentage(self) -> int:
        if not self.is_on:
            return 0
        return pump_speed_to_percentage(
            int(self.coordinator.data.get("pump_speed", PUMP_SPEED_MIN))
        )

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        values = {PIN_POWER: 1}
        if percentage is not None and percentage > 0:
            values[PIN_PUMP_SPEED] = pump_percentage_to_speed(percentage)
        await self._write_pins(values)
        await self.coordinator.async_request_refresh_soon()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._write_pins({PIN_POWER: 0})
        await self.coordinator.async_request_refresh_soon()

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            await self.async_turn_off()
            return
        values = {PIN_PUMP_SPEED: pump_percentage_to_speed(percentage)}
        if not self.is_on:
            values[PIN_POWER] = 1
        await self._write_pins(values)
        await self.coordinator.async_request_refresh_soon()

    async def _write_pins(self, values: dict[str, int]) -> None:
        try:
            await self.coordinator.client.write_pins(values)
        except AquascapeAPIError as err:
            raise HomeAssistantError(str(err)) from err

        data = dict(self.coordinator.data)
        if PIN_POWER in values:
            data["power"] = values[PIN_POWER] == 1
        if PIN_PUMP_SPEED in values:
            data["pump_speed"] = values[PIN_PUMP_SPEED]
        self.coordinator.async_set_updated_data(data)
