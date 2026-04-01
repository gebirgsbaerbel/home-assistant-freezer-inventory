"""Freezer Inventory sensor platform."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)

from .const import (
    CONF_LIST_TYPE,
    CONF_NAME,
    CONF_TODO_ENTITY_ID,
    DOMAIN,
    EVENT_FREEZER_REFRESH,
    LIST_TYPE_SHOPPING,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freezer Inventory sensor from a config entry."""
    todo_entity_id = entry.data[CONF_TODO_ENTITY_ID]
    list_type = entry.data.get(CONF_LIST_TYPE, "inventory")
    name = entry.data.get(CONF_NAME, entry.title)
    sensor = FreezerInventorySensor(hass, todo_entity_id, list_type, name)
    hass.data[DOMAIN][entry.entry_id] = sensor
    async_add_entities([sensor])


class FreezerInventorySensor(SensorEntity):
    """Sensor that mirrors a todo list as an inventory or shopping list."""

    _attr_icon = "mdi:fridge"

    def __init__(self, hass: HomeAssistant, todo_entity_id: str, list_type: str, name: str) -> None:
        self._todo_entity_id = todo_entity_id
        self._list_type = list_type
        self._items: list[dict] = []
        self.hass = hass
        self._attr_unique_id = f"freezer_inventory_{todo_entity_id}"
        self._attr_name = name

    async def async_added_to_hass(self) -> None:
        """Register event listeners once added to hass."""
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._todo_entity_id],
                self._handle_state_change,
            )
        )
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_FREEZER_REFRESH, self._handle_refresh_event)
        )
        self.async_on_remove(
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, self._handle_ha_start)
        )
        self.async_on_remove(
            async_track_time_interval(self.hass, self._handle_time_interval, SCAN_INTERVAL)
        )

        if self.hass.is_running:
            self.hass.async_create_task(self._async_refresh())

    @callback
    def _handle_state_change(self, event: Event) -> None:
        self.hass.async_create_task(self._async_refresh())

    @callback
    def _handle_refresh_event(self, event: Event) -> None:
        self.hass.async_create_task(self._async_refresh())

    @callback
    def _handle_ha_start(self, event: Event) -> None:
        self.hass.async_create_task(self._async_refresh())

    @callback
    def _handle_time_interval(self, now) -> None:
        self.hass.async_create_task(self._async_refresh())

    async def _async_refresh(self) -> None:
        """Fetch items from the todo list and update state."""
        try:
            response = await self.hass.services.async_call(
                "todo",
                "get_items",
                {"entity_id": self._todo_entity_id},
                blocking=True,
                return_response=True,
            )
        except Exception as err:
            _LOGGER.error("Failed to fetch todo items from %s: %s", self._todo_entity_id, err)
            return

        raw_items = (response or {}).get(self._todo_entity_id, {}).get("items", [])

        if self._list_type == LIST_TYPE_SHOPPING:
            parsed = [
                {
                    "description": item.get("summary", ""),
                    "uid": item.get("uid", ""),
                    "detail": item.get("description", ""),
                }
                for item in raw_items
                if item.get("summary", "").strip() and item.get("status") != "completed"
            ]
        else:
            parsed = []
            for item in raw_items:
                try:
                    portions = int(item.get("description") or 0)
                except (ValueError, TypeError):
                    portions = 0
                if portions <= 0:
                    continue
                parsed.append(
                    {
                        "description": item.get("summary", ""),
                        "uid": item.get("uid", ""),
                        "expiration": item.get("due"),
                        "portions": portions,
                    }
                )
            parsed.sort(key=lambda x: (x["expiration"] is None, x["expiration"] or "", x["portions"]))

        self._items = parsed
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        return len(self._items)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "items": self._items,
            "todo_entity_id": self._todo_entity_id,
            "list_type": self._list_type,
        }
