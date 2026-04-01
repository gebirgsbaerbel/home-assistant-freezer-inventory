"""Freezer Inventory integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_TODO_ENTITY_ID,
    DOMAIN,
    EVENT_FREEZER_REFRESH,
    SERVICE_FREEZER_MINUS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Freezer Inventory from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_FREEZER_MINUS):
        _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_FREEZER_MINUS)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    """Register integration services."""

    async def handle_freezer_minus(call) -> None:
        """Decrement portions for a named freezer item by one."""
        item_name = call.data["item"]
        portions = call.data["portions"]
        new_portions = max(int(portions) - 1, 0)

        for sensor in hass.data[DOMAIN].values():
            uid = next(
                (i["uid"] for i in sensor._items if i["description"] == item_name),
                None,
            )
            if uid is not None:
                await hass.services.async_call(
                    "todo",
                    "update_item",
                    {
                        "entity_id": sensor._todo_entity_id,
                        "item": uid,
                        "description": str(new_portions),
                    },
                    blocking=True,
                )
                hass.bus.async_fire(EVENT_FREEZER_REFRESH)
                return

        _LOGGER.error("freezer_minus: item '%s' not found in any configured list", item_name)

    hass.services.async_register(
        DOMAIN,
        SERVICE_FREEZER_MINUS,
        handle_freezer_minus,
        schema=vol.Schema(
            {
                vol.Required("item"): cv.string,
                vol.Required("portions"): vol.Coerce(int),
            }
        ),
    )
