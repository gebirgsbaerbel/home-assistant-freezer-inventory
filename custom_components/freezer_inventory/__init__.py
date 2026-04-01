"""Freezer Inventory integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
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
_CARD_URL = "/freezer_inventory/freezer-inventory-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the static path for the Lovelace card JS file."""
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            url_path=_CARD_URL,
            path=hass.config.path("custom_components/freezer_inventory/www/freezer-inventory-card.js"),
            cache_headers=False,
        )
    ])
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Freezer Inventory from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_FREEZER_MINUS):
        _register_services(hass)

    if not hass.data[DOMAIN].get("_lovelace_registered"):
        hass.data[DOMAIN]["_lovelace_registered"] = True
        if hass.is_running:
            await _async_ensure_lovelace_resource(hass)
        else:
            async def _on_started(event):
                await _async_ensure_lovelace_resource(hass)
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not any(not k.startswith("_") for k in hass.data[DOMAIN]):
            hass.services.async_remove(DOMAIN, SERVICE_FREEZER_MINUS)
    return unload_ok


async def _async_ensure_lovelace_resource(hass: HomeAssistant) -> None:
    """Add the card JS as a Lovelace resource if not already registered."""
    try:
        lovelace = hass.data.get("lovelace")
        if not lovelace:
            _LOGGER.warning("Lovelace not available; add %s as a module resource manually.", _CARD_URL)
            return
        resources = getattr(lovelace, "resources", None)
        if not resources:
            _LOGGER.warning("Lovelace resources unavailable; add %s as a module resource manually.", _CARD_URL)
            return
        await resources.async_load()
        if not any(r["url"] == _CARD_URL for r in resources.async_items()):
            await resources.async_create_item({"res_type": "module", "url": _CARD_URL})
            _LOGGER.info("Registered Lovelace resource: %s", _CARD_URL)
    except Exception as err:
        _LOGGER.warning(
            "Could not auto-register Lovelace resource (%s); add %s as a module resource manually.",
            err, _CARD_URL,
        )


def _register_services(hass: HomeAssistant) -> None:
    """Register integration services."""

    async def handle_freezer_minus(call) -> None:
        """Decrement portions for a named freezer item by one."""
        item_name = call.data["item"]
        portions = call.data["portions"]
        new_portions = max(int(portions) - 1, 0)

        for key, sensor in hass.data[DOMAIN].items():
            if key.startswith("_"):
                continue
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
