"""Constants for the Couch Control integration."""
from __future__ import annotations

DOMAIN = "couch_control"

# Configuration
CONF_SELECTED_ENTITIES = "selected_entities"

# WebSocket API types
WS_TYPE_SUBSCRIBE_FILTERED = "couch_control/subscribe_filtered"
WS_TYPE_GET_ENTITIES = "couch_control/get_entities"
WS_TYPE_UPDATE_ENTITIES = "couch_control/update_entities"

# Storage
STORAGE_KEY = "couch_control.entities"
STORAGE_VERSION = 1

# Defaults
DEFAULT_NAME = "Couch Control"