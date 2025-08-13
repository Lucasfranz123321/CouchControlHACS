"""Constants for Couch Control."""

DOMAIN = "couch_control"
STORAGE_KEY = "couch_control"
STORAGE_VERSION = 1

CONF_ENTITIES = "entities"
CONF_FILTER_MODE = "filter_mode"

FILTER_MODE_INCLUDE = "include"
FILTER_MODE_EXCLUDE = "exclude"

WS_TYPE_SUBSCRIBE_FILTERED = f"{DOMAIN}/subscribe_filtered"
WS_TYPE_GET_ENTITIES = f"{DOMAIN}/get_entities"
WS_TYPE_UPDATE_ENTITIES = f"{DOMAIN}/update_entities"