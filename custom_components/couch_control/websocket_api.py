"""WebSocket API for Couch Control filtered subscriptions."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    WS_TYPE_GET_ENTITIES,
    WS_TYPE_SUBSCRIBE_FILTERED,
    WS_TYPE_UPDATE_ENTITIES,
)
from .storage import async_save_entities

_LOGGER = logging.getLogger(__name__)


async def async_setup_websocket_api(hass: HomeAssistant) -> None:
    """Set up WebSocket API commands."""
    websocket_api.async_register_command(hass, handle_subscribe_filtered)
    websocket_api.async_register_command(hass, handle_get_entities)
    websocket_api.async_register_command(hass, handle_update_entities)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_SUBSCRIBE_FILTERED,
    }
)
@callback
def handle_subscribe_filtered(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle filtered entity subscription."""
    
    @callback
    def forward_events(event: Event) -> None:
        """Forward filtered state change events to the client."""
        # Get the list of allowed entities
        allowed_entities = hass.data[DOMAIN].get("entities", [])
        
        # Check if this entity is allowed
        entity_id = event.data.get("entity_id")
        if entity_id not in allowed_entities:
            return
        
        # Get old and new state
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        
        # Format the event for the client
        event_message = {
            "id": msg["id"],
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": entity_id,
                    "old_state": _state_to_dict(old_state) if old_state else None,
                    "new_state": _state_to_dict(new_state) if new_state else None,
                },
                "origin": event.origin,
                "time_fired": event.time_fired.isoformat(),
            },
        }
        
        connection.send_message(websocket_api.messages.event_message(msg["id"], event_message["event"]))
    
    # Send initial states for allowed entities
    allowed_entities = hass.data[DOMAIN].get("entities", [])
    states = []
    
    for entity_id in allowed_entities:
        state = hass.states.get(entity_id)
        if state:
            states.append(_state_to_dict(state))
    
    connection.send_result(msg["id"], {"states": states})
    
    # Track state changes for allowed entities only
    unsub = async_track_state_change_event(
        hass, allowed_entities, forward_events
    )
    
    # Handle unsubscribe
    connection.subscriptions[msg["id"]] = unsub
    
    _LOGGER.info(
        "Client subscribed to filtered updates for %d entities", len(allowed_entities)
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_GET_ENTITIES,
    }
)
@callback
def handle_get_entities(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle request to get list of filtered entities."""
    entities = hass.data[DOMAIN].get("entities", [])
    
    # Get entity registry
    ent_reg = er.async_get(hass)
    
    # Build detailed entity information
    entity_info = []
    for entity_id in entities:
        state = hass.states.get(entity_id)
        entry = ent_reg.async_get(entity_id)
        
        info = {
            "entity_id": entity_id,
            "state": state.state if state else None,
            "attributes": dict(state.attributes) if state else {},
        }
        
        if entry:
            info.update({
                "name": entry.name or entry.original_name,
                "icon": entry.icon or entry.original_icon,
                "device_class": entry.device_class,
                "unit_of_measurement": entry.unit_of_measurement,
            })
        
        entity_info.append(info)
    
    connection.send_result(msg["id"], {"entities": entity_info})


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_UPDATE_ENTITIES,
        vol.Required("entities"): [str],
    }
)
@callback
def handle_update_entities(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle request to update filtered entities."""
    entities = msg["entities"]
    
    # Validate entities exist
    valid_entities = []
    for entity_id in entities:
        if hass.states.get(entity_id) is not None:
            valid_entities.append(entity_id)
        else:
            _LOGGER.warning("Entity %s does not exist", entity_id)
    
    # Update stored entities
    hass.data[DOMAIN]["entities"] = valid_entities
    hass.async_create_task(
        async_save_entities(hass, {"entities": valid_entities})
    )
    
    connection.send_result(
        msg["id"], 
        {
            "success": True, 
            "entities": valid_entities,
            "filtered_count": len(entities) - len(valid_entities)
        }
    )
    
    _LOGGER.info("Updated filtered entities list with %d entities", len(valid_entities))


def _state_to_dict(state: State) -> dict[str, Any]:
    """Convert state to dictionary representation."""
    return {
        "entity_id": state.entity_id,
        "state": state.state,
        "attributes": dict(state.attributes),
        "last_changed": state.last_changed.isoformat(),
        "last_updated": state.last_updated.isoformat(),
    }