"""Freezer Inventory sensor platform."""
from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

CONF_TODO_ENTITY_ID = "todo_entity_id"
DEFAULT_TODO_ENTITY_ID = "todo.freezer"
SCAN_INTERVAL = timedelta(minutes=10)
EVENT_FREEZER_REFRESH = "freezer_refresh"
SERVICE_FREEZER_MINUS = "freezer_minus"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_TODO_ENTITY_ID, default=DEFAULT_TODO_ENTITY_ID): cv.entity_id,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Freezer Inventory sensor."""
    todo_entity_id = config[CONF_TODO_ENTITY_ID]
    sensor = FreezerInventorySensor(hass, todo_entity_id)
    async_add_entities([sensor])

    async def handle_freezer_minus(call) -> None:
        """Decrement portions for a named freezer item."""
        item_name = call.data["item"]
        portions = call.data["portions"]
        new_portions = max(int(portions) - 1, 0)

        uid = next(
            (i["uid"] for i in sensor._items if i["description"] == item_name),
            None,
        )
        if uid is None:
            _LOGGER.error("freezer_minus: item '%s' not found in cached items", item_name)
            return

        await hass.services.async_call(
            "todo",
            "update_item",
            {
                "entity_id": todo_entity_id,
                "item": uid,
                "description": str(new_portions),
            },
            blocking=True,
        )
        hass.bus.async_fire(EVENT_FREEZER_REFRESH)

    hass.services.async_register(
        "freezer_inventory",
        SERVICE_FREEZER_MINUS,
        handle_freezer_minus,
        schema=vol.Schema(
            {
                vol.Required("item"): cv.string,
                vol.Required("portions"): vol.Coerce(int),
            }
        ),
    )


class FreezerInventorySensor(SensorEntity):
    """Sensor that mirrors a todo list as freezer inventory."""

    _attr_icon = "mdi:fridge"

    def __init__(self, hass: HomeAssistant, todo_entity_id: str) -> None:
        self._todo_entity_id = todo_entity_id
        self._items: list[dict] = []
        self.hass = hass
        self._attr_name = "Freezer Inventory"
        self._attr_unique_id = f"freezer_inventory_{todo_entity_id}"

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

        # If HA is already running (e.g. after a reload), do an immediate fetch
        # because EVENT_HOMEASSISTANT_START won't fire again
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

        # Sort by expiration (None last), then by portions ascending
        parsed.sort(key=lambda x: (x["expiration"] is None, x["expiration"] or "", x["portions"]))
        self._items = parsed
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        return len(self._items)

    @property
    def extra_state_attributes(self) -> dict:
        return {"items": self._items}
