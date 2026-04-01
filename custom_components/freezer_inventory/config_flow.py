"""Config flow for Freezer Inventory."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_LIST_TYPE,
    CONF_NAME,
    CONF_TODO_ENTITY_ID,
    DOMAIN,
    LIST_TYPE_INVENTORY,
    LIST_TYPE_SHOPPING,
)


class FreezerInventoryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Freezer Inventory."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_TODO_ENTITY_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_TODO_ENTITY_ID): EntitySelector(
                        EntitySelectorConfig(domain="todo")
                    ),
                    vol.Required(CONF_LIST_TYPE, default=LIST_TYPE_INVENTORY): SelectSelector(
                        SelectSelectorConfig(
                            options=[LIST_TYPE_INVENTORY, LIST_TYPE_SHOPPING],
                            mode=SelectSelectorMode.LIST,
                            translation_key="list_type",
                        )
                    ),
                }
            ),
        )
