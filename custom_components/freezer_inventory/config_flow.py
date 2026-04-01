"""Config flow for Freezer Inventory."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import CONF_TODO_ENTITY_ID, DOMAIN


class FreezerInventoryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Freezer Inventory."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_TODO_ENTITY_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_TODO_ENTITY_ID],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TODO_ENTITY_ID): EntitySelector(
                        EntitySelectorConfig(domain="todo")
                    ),
                }
            ),
        )
