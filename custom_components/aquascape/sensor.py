"""Diagnostic sensors for Aquascape hubs."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN, MANUFACTURER, MODEL
from .coordinator import AquascapeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AquascapeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AquascapeRssiSensor(coordinator)])


class AquascapeRssiSensor(CoordinatorEntity[AquascapeCoordinator], SensorEntity):
    """WiFi signal strength reported by the hub (V30)."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "rssi"
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: AquascapeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_rssi"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.data[CONF_NAME],
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def native_value(self) -> int:
        return round(self.coordinator.data.get("rssi", -100))
