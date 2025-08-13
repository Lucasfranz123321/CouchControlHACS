"""Storage handling for Couch Control."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)


async def async_load_entities(hass: HomeAssistant) -> dict[str, Any]:
    """Load entities from storage."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    
    try:
        data = await store.async_load()
        if data is None:
            return {"entities": []}
        return data
    except Exception:
        _LOGGER.exception("Error loading entities from storage")
        return {"entities": []}


async def async_save_entities(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Save entities to storage."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    
    try:
        await store.async_save(data)
    except Exception:
        _LOGGER.exception("Error saving entities to storage")