"""Couch Control integration for Home Assistant."""
import logging
from aiohttp import web
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN, CONF_SELECTED_ENTITIES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Couch Control from a config entry."""
    _LOGGER.info(f"Setting up Couch Control integration: {entry.title}")
    
    # Store the entry data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry
    
    # Only register views once
    if "views_registered" not in hass.data[DOMAIN]:
        # Register the API endpoint for filtered states
        hass.http.register_view(CouchControlStatesView(hass))
        
        # Register info endpoint
        hass.http.register_view(CouchControlInfoView())
        
        hass.data[DOMAIN]["views_registered"] = True
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Couch Control integration")
    
    # Clean up
    hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return True

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry
) -> bool:
    """Remove a config entry from a device."""
    return True

class CouchControlStatesView(HomeAssistantView):
    """API view for filtered entity states."""
    
    url = "/api/couch_control/states"
    name = "api:couch_control:states"
    requires_auth = True
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the view."""
        self.hass = hass

    async def get(self, request):
        """Return filtered states for Couch Control."""
        try:
            # Collect entities from all config entries
            all_selected_entities = set()
            
            for entry_id, entry in self.hass.data[DOMAIN].items():
                if entry_id == "views_registered":
                    continue
                    
                selected_entities = entry.options.get(CONF_SELECTED_ENTITIES, [])
                if not selected_entities:
                    selected_entities = entry.data.get(CONF_SELECTED_ENTITIES, [])
                
                all_selected_entities.update(selected_entities)
            
            # Filter states to only include selected entities
            filtered_states = []
            for entity_id in all_selected_entities:
                state = self.hass.states.get(entity_id)
                if state:
                    filtered_states.append(state.as_dict())
            
            _LOGGER.info(f"Couch Control: Returning {len(filtered_states)} filtered entities from {len(self.hass.data[DOMAIN]) - 1} config entries")
            return web.json_response(filtered_states)
            
        except Exception as e:
            _LOGGER.error(f"Error in Couch Control states endpoint: {e}")
            return web.json_response({"error": str(e)}, status=500)

class CouchControlInfoView(HomeAssistantView):
    """Info endpoint to detect integration presence."""
    
    url = "/api/couch_control/info"
    name = "api:couch_control:info"
    requires_auth = True

    async def get(self, request):
        """Return integration info."""
        return web.json_response({
            "integration": "couch_control",
            "version": "1.0.0",
            "status": "active"
        })