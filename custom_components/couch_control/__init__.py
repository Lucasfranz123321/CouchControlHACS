"""Couch Control Entity Filter for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import persistent_notification, websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION, CONF_ENTITIES
from .storage import async_load_entities, async_save_entities
from .websocket_api import async_setup_websocket_api
from .api import async_setup_api

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Couch Control component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Couch Control from a config entry."""
    try:
        hass.data.setdefault(DOMAIN, {})
        
        # Load stored entity selections
        try:
            stored_entities = await async_load_entities(hass)
            entities = stored_entities.get("entities", [])
        except Exception as ex:
            _LOGGER.exception("Error loading stored entities, using config data")
            entities = entry.data.get(CONF_ENTITIES, [])
        
        hass.data[DOMAIN]["entities"] = entities
        hass.data[DOMAIN]["entry"] = entry
        
        # Set up WebSocket API
        try:
            await async_setup_websocket_api(hass)
        except Exception as ex:
            _LOGGER.exception("Error setting up WebSocket API")
            return False
        
        # Set up REST API
        try:
            await async_setup_api(hass)
        except Exception as ex:
            _LOGGER.exception("Error setting up REST API")
            return False
        
        # Register services
        try:
            await _async_setup_services(hass)
        except Exception as ex:
            _LOGGER.exception("Error setting up services")
            return False
        
        # Add update listener
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))
        
        _LOGGER.info("Couch Control Entity Filter setup completed successfully")
        return True
        
    except Exception as ex:
        _LOGGER.exception("Error setting up Couch Control integration")
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        # Remove services (with error handling)
        try:
            hass.services.async_remove(DOMAIN, "add_entity")
            hass.services.async_remove(DOMAIN, "remove_entity")
            hass.services.async_remove(DOMAIN, "set_entities")
            hass.services.async_remove(DOMAIN, "uninstall")
        except Exception as ex:
            _LOGGER.warning("Error removing services during unload: %s", ex)

        # Pop the domain entirely instead of `clear()` so no empty
        # container is left behind for handlers that test
        # `if DOMAIN in hass.data`. Note that WebSocket commands and
        # REST views registered during setup cannot be unregistered
        # in HA — they're guarded inside their handlers to no-op
        # when the domain is gone, so they degrade cleanly until HA
        # restarts.
        hass.data.pop(DOMAIN, None)

        _LOGGER.info("Couch Control Entity Filter unloaded successfully")
        return True

    except Exception as ex:
        _LOGGER.exception("Error unloading Couch Control integration")
        return False


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete persisted storage when the user removes the integration.

    Without this, the entity-selection list at `.storage/couch_control`
    survives the deletion. The next time the user re-adds Couch
    Control the config flow loads that file and pre-populates the
    form with the old entities — which is what made the integration
    feel like it 'kept staying' after the user clicked Delete.
    """
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    try:
        await store.async_remove()
        _LOGGER.info("Couch Control storage removed during integration removal")
    except Exception:
        _LOGGER.exception("Error removing Couch Control storage")


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Couch Control."""
    
    @callback
    def add_entity(call):
        """Add an entity to the filter list."""
        entity_id = call.data.get("entity_id")
        if entity_id and entity_id not in hass.data[DOMAIN]["entities"]:
            hass.data[DOMAIN]["entities"].append(entity_id)
            hass.async_create_task(
                async_save_entities(hass, {"entities": hass.data[DOMAIN]["entities"]})
            )
            _LOGGER.info("Added %s to Couch Control filter", entity_id)
    
    @callback
    def remove_entity(call):
        """Remove an entity from the filter list."""
        entity_id = call.data.get("entity_id")
        if entity_id in hass.data[DOMAIN]["entities"]:
            hass.data[DOMAIN]["entities"].remove(entity_id)
            hass.async_create_task(
                async_save_entities(hass, {"entities": hass.data[DOMAIN]["entities"]})
            )
            _LOGGER.info("Removed %s from Couch Control filter", entity_id)
    
    @callback
    def set_entities(call):
        """Set the complete entity filter list."""
        entities = call.data.get("entities", [])
        hass.data[DOMAIN]["entities"] = entities
        hass.async_create_task(
            async_save_entities(hass, {"entities": entities})
        )
        _LOGGER.info("Updated Couch Control filter with %d entities", len(entities))

    async def uninstall(call):
        """Clean uninstall: remove the config entry while the
        integration code is still loaded.

        Why this exists: when a user removes the integration via HACS,
        HA can no longer execute `async_unload_entry` /
        `async_remove_entry` because the module is gone — leaving an
        orphaned config entry and the persisted storage file behind.
        Running this service first triggers the normal HA removal
        path (which calls our `async_remove_entry`, which deletes
        `.storage/couch_control`), so the subsequent HACS file
        deletion has nothing to mop up.
        """
        entry = hass.data.get(DOMAIN, {}).get("entry")
        if entry is None:
            _LOGGER.warning(
                "Couch Control uninstall called but no config entry "
                "was found — already uninstalled?"
            )
            return
        entry_id = entry.entry_id
        _LOGGER.info(
            "Couch Control uninstall service called — removing config "
            "entry %s and persisted storage", entry_id
        )
        await hass.config_entries.async_remove(entry_id)
        _LOGGER.info(
            "Couch Control config entry removed. You can now delete "
            "the integration from HACS to remove the files."
        )
        # Surface a persistent notification so the user sees it without
        # tailing logs — the typical user calls this from the UI and
        # never sees `_LOGGER.info` output.
        persistent_notification.async_create(
            hass,
            (
                "Couch Control has been removed from Home Assistant. "
                "Open HACS → Couch Control → Remove to delete the "
                "integration files, then restart Home Assistant."
            ),
            title="Couch Control uninstalled",
            notification_id=f"{DOMAIN}_uninstalled",
        )

    hass.services.async_register(DOMAIN, "add_entity", add_entity)
    hass.services.async_register(DOMAIN, "remove_entity", remove_entity)
    hass.services.async_register(DOMAIN, "set_entities", set_entities)
    hass.services.async_register(DOMAIN, "uninstall", uninstall)