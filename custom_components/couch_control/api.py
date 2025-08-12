"""REST API for Couch Control Entity Filter."""
from __future__ import annotations

import logging
from typing import Any

from aiohttp import web
import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .storage import async_save_entities

_LOGGER = logging.getLogger(__name__)


class CouchControlEntitiesView(HomeAssistantView):
    """View to handle Couch Control entities API."""

    url = "/api/couch_control/entities"
    name = "api:couch_control:entities"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        """Get filtered entities list."""
        hass = request.app["hass"]
        
        if DOMAIN not in hass.data:
            return web.json_response(
                {"error": "Couch Control not configured"}, status=400
            )
        
        entities = hass.data[DOMAIN].get("entities", [])
        
        # Get detailed entity information
        ent_reg = er.async_get(hass)
        detailed_entities = []
        
        for entity_id in entities:
            state = hass.states.get(entity_id)
            entry = ent_reg.async_get(entity_id)
            
            entity_data = {
                "entity_id": entity_id,
                "state": state.state if state else None,
                "attributes": dict(state.attributes) if state else {},
                "last_changed": state.last_changed.isoformat() if state else None,
                "last_updated": state.last_updated.isoformat() if state else None,
            }
            
            if entry:
                entity_data.update({
                    "name": entry.name or entry.original_name,
                    "icon": entry.icon or entry.original_icon,
                    "device_class": entry.device_class,
                    "unit_of_measurement": entry.unit_of_measurement,
                    "area_id": entry.area_id,
                    "device_id": entry.device_id,
                })
            
            detailed_entities.append(entity_data)
        
        return web.json_response({
            "entities": detailed_entities,
            "count": len(entities)
        })

    async def post(self, request: web.Request) -> web.Response:
        """Update filtered entities list."""
        hass = request.app["hass"]
        
        if DOMAIN not in hass.data:
            return web.json_response(
                {"error": "Couch Control not configured"}, status=400
            )
        
        try:
            data = await request.json()
        except Exception:
            return web.json_response(
                {"error": "Invalid JSON"}, status=400
            )
        
        # Validate schema
        schema = vol.Schema({
            vol.Required("entities"): [str],
        })
        
        try:
            validated_data = schema(data)
        except vol.Invalid as err:
            return web.json_response(
                {"error": f"Invalid data: {err}"}, status=400
            )
        
        entities = validated_data["entities"]
        
        # Validate entities exist
        valid_entities = []
        invalid_entities = []
        
        for entity_id in entities:
            if hass.states.get(entity_id) is not None:
                valid_entities.append(entity_id)
            else:
                invalid_entities.append(entity_id)
        
        # Update storage
        hass.data[DOMAIN]["entities"] = valid_entities
        await async_save_entities(hass, {"entities": valid_entities})
        
        response_data = {
            "success": True,
            "entities": valid_entities,
            "count": len(valid_entities),
        }
        
        if invalid_entities:
            response_data["invalid_entities"] = invalid_entities
            response_data["warning"] = f"{len(invalid_entities)} invalid entities were filtered out"
        
        _LOGGER.info("Updated Couch Control entities via API: %d entities", len(valid_entities))
        
        return web.json_response(response_data)


class CouchControlInfoView(HomeAssistantView):
    """View to provide Couch Control integration info."""

    url = "/api/couch_control/info"
    name = "api:couch_control:info"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        """Get integration information."""
        hass = request.app["hass"]
        
        if DOMAIN not in hass.data:
            return web.json_response(
                {"error": "Couch Control not configured"}, status=400
            )
        
        entity_count = len(hass.data[DOMAIN].get("entities", []))
        
        return web.json_response({
            "integration": "Couch Control Entity Filter",
            "version": "1.0.0",
            "domain": DOMAIN,
            "filtered_entities_count": entity_count,
            "websocket_endpoint": f"{DOMAIN}/subscribe_filtered",
            "status": "active"
        })


class CouchControlClearView(HomeAssistantView):
    """View to clear all filtered entities."""

    url = "/api/couch_control/clear"
    name = "api:couch_control:clear"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        """Clear all filtered entities."""
        hass = request.app["hass"]
        
        if DOMAIN not in hass.data:
            return web.json_response(
                {"error": "Couch Control not configured"}, status=400
            )
        
        # Clear stored entities
        hass.data[DOMAIN]["entities"] = []
        await async_save_entities(hass, {"entities": []})
        
        _LOGGER.info("Couch Control: Cleared all filtered entities via clear endpoint")
        
        return web.json_response({
            "success": True,
            "message": "All filtered entities cleared"
        })


async def async_setup_api(hass: HomeAssistant) -> None:
    """Set up the REST API."""
    hass.http.register_view(CouchControlEntitiesView())
    hass.http.register_view(CouchControlInfoView())
    hass.http.register_view(CouchControlClearView())
    
    _LOGGER.info("Couch Control REST API endpoints registered")