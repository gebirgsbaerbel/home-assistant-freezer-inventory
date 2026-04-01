"""Freezer Inventory sensor platform."""
from homeassistant.components.sensor import SensorEntity

PLATFORM_SCHEMA = {}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Freezer Inventory sensor."""
    async_add_entities([FreezerInventoryHelloSensor()])


class FreezerInventoryHelloSensor(SensorEntity):
    """A placeholder sensor for the Freezer Inventory integration."""

    _attr_unique_id = "freezer_inventory_hello"
    _attr_name = "Freezer Inventory"
    _attr_icon = "mdi:fridge"

    @property
    def native_value(self):
        return "Hello from Freezer Inventory!"
