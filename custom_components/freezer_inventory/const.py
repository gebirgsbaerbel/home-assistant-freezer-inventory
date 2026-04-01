"""Constants for the Freezer Inventory integration."""
from datetime import timedelta

DOMAIN = "freezer_inventory"
CONF_TODO_ENTITY_ID = "todo_entity_id"
CONF_LIST_TYPE = "list_type"
CONF_NAME = "name"
LIST_TYPE_INVENTORY = "inventory"
LIST_TYPE_SHOPPING = "shopping"
SCAN_INTERVAL = timedelta(minutes=10)
EVENT_FREEZER_REFRESH = "freezer_refresh"
SERVICE_FREEZER_MINUS = "freezer_minus"
