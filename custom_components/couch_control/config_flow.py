"""Config flow for Couch Control Entity Filter integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er, area_registry as ar, device_registry as dr, config_validation as cv
from homeassistant.helpers.service import async_call_from_config

from .const import CONF_ENTITIES, DOMAIN
from .storage import async_load_entities, async_save_entities

_LOGGER = logging.getLogger(__name__)


class CouchControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Couch Control Entity Filter."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._entities: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Store the selected entities
                entities = user_input.get(CONF_ENTITIES, [])
                
                # Filter out header keys (they're not selectable entities)
                entities = [e for e in entities if not e.startswith("_AREA_HEADER_")]
                self._entities = entities
                
                # Validate entities exist
                ent_reg = er.async_get(self.hass)
                valid_entities = []
                for entity_id in self._entities:
                    if entity_id in ent_reg.entities or self.hass.states.get(entity_id):
                        valid_entities.append(entity_id)
                    else:
                        _LOGGER.warning("Entity %s does not exist, removing from selection", entity_id)
                
                # Save the valid entities to storage
                await async_save_entities(self.hass, {"entities": valid_entities})
                
                # Store entities for success step
                self._entities = valid_entities
                
                # Go to success step instead of creating entry directly
                return await self.async_step_success()
            except Exception as ex:
                _LOGGER.exception("Error creating config entry")
                errors["base"] = "unknown"

        try:
            # Get all available entities organized by areas/rooms
            ent_reg = er.async_get(self.hass)
            area_reg = ar.async_get(self.hass)
            dev_reg = dr.async_get(self.hass)
            
            # Group entities by area/room
            entities_by_area = {}
            no_area_entities = {}
            
            for entry in ent_reg.entities.values():
                if entry.disabled:
                    continue
                    
                # Create display name with entity ID and integration
                friendly_name = entry.name or entry.original_name or entry.entity_id
                entity_id = entry.entity_id
                
                # Get the integration/platform name
                platform = entry.platform if entry.platform else "unknown"
                
                # Format: "Friendly Name - entity.id (integration)"
                display_name = f"{friendly_name} - {entity_id} ({platform})"
                
                # Group by area/room - check both entity area and device area
                area_name = None
                try:
                    # First check if entity is directly assigned to an area
                    if entry.area_id:
                        area = area_reg.async_get_area(entry.area_id)
                        if area:
                            area_name = area.name
                    # If no direct entity area, check device area
                    elif entry.device_id:
                        device = dev_reg.async_get(entry.device_id)
                        if device and device.area_id:
                            area = area_reg.async_get_area(device.area_id)
                            if area:
                                area_name = area.name
                except Exception:
                    pass
                
                if area_name:
                    if area_name not in entities_by_area:
                        entities_by_area[area_name] = {}
                    entities_by_area[area_name][entity_id] = display_name
                else:
                    no_area_entities[entity_id] = display_name
            
            # Create organized entity list
            all_entities = {}
            
            # Add entities grouped by area (sorted alphabetically by area name)
            for area_name in sorted(entities_by_area.keys()):
                area_entities = entities_by_area[area_name]
                # Add area header
                area_header_key = f"_AREA_HEADER_{area_name}"
                all_entities[area_header_key] = f"🏠 {area_name} ({len(area_entities)} items) - Header Not Selectable"
                
                # Add entities in this area (sorted alphabetically)
                for entity_id in sorted(area_entities.keys()):
                    all_entities[entity_id] = f"    {area_entities[entity_id]}"
            
            # Add entities with no area at the end
            if no_area_entities:
                # Add "No Area" header
                no_area_header_key = "_AREA_HEADER_NO_AREA"
                all_entities[no_area_header_key] = f"🚫 No Area Assigned ({len(no_area_entities)} items) - Header Not Selectable"
                
                # Add entities without area (sorted alphabetically)
                for entity_id in sorted(no_area_entities.keys()):
                    all_entities[entity_id] = f"    {no_area_entities[entity_id]}"

            # Load existing selections (with error handling)
            try:
                existing_data = await async_load_entities(self.hass)
                existing_entities = existing_data.get("entities", [])
            except Exception as ex:
                _LOGGER.exception("Error loading existing entities")
                existing_entities = []

            # Filter out header keys for counting and validation
            selectable_entities = {k: v for k, v in all_entities.items() if not k.startswith("_AREA_HEADER_")}

            if not selectable_entities:
                errors["base"] = "no_entities"

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_ENTITIES, default=existing_entities
                        ): cv.multi_select(all_entities),
                    }
                ),
                errors=errors,
                description_placeholders={
                    "entity_count": str(len(selectable_entities)),
                },
            )
        except Exception as ex:
            _LOGGER.exception("Error in config flow")
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({}),
                errors={"base": "unknown"},
            )

    async def async_step_success(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the success step with restart option."""
        if user_input is not None:
            if user_input.get("restart", False):
                # Restart Home Assistant
                try:
                    await self.hass.services.async_call(
                        "homeassistant", "restart", {}, blocking=False
                    )
                except Exception as ex:
                    _LOGGER.exception("Error restarting Home Assistant")
            
            # Create the config entry
            return self.async_create_entry(
                title="Couch Control Entity Filter",
                data={
                    CONF_ENTITIES: self._entities,
                },
            )
        
        # Show success form with restart option
        return self.async_show_form(
            step_id="success",
            data_schema=vol.Schema(
                {
                    vol.Optional("restart", default=True): bool,
                }
            ),
            description_placeholders={
                "entity_count": str(len(self._entities)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CouchControlOptionsFlow:
        """Create the options flow."""
        return CouchControlOptionsFlow(config_entry)


class CouchControlOptionsFlow(config_entries.OptionsFlow):
    """Handle Couch Control options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._entities: list[str] = []

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Save the updated entities
                entities = user_input.get(CONF_ENTITIES, [])
                
                # Filter out header keys (they're not selectable entities)
                entities = [e for e in entities if not e.startswith("_AREA_HEADER_")]
                
                # Validate entities exist
                ent_reg = er.async_get(self.hass)
                valid_entities = []
                for entity_id in entities:
                    if entity_id in ent_reg.entities or self.hass.states.get(entity_id):
                        valid_entities.append(entity_id)
                    else:
                        _LOGGER.warning("Entity %s does not exist, removing from selection", entity_id)
                
                await async_save_entities(self.hass, {"entities": valid_entities})
                
                # Update hass data if available
                if DOMAIN in self.hass.data:
                    self.hass.data[DOMAIN]["entities"] = valid_entities
                
                # Store entities for success step
                self._entities = valid_entities
                
                # Go to success step instead of creating entry directly
                return await self.async_step_success()
            except Exception as ex:
                _LOGGER.exception("Error updating options")
                errors["base"] = "unknown"

        try:
            # Get all available entities organized by areas/rooms
            ent_reg = er.async_get(self.hass)
            area_reg = ar.async_get(self.hass)
            dev_reg = dr.async_get(self.hass)
            
            # Group entities by area/room
            entities_by_area = {}
            no_area_entities = {}
            
            for entry in ent_reg.entities.values():
                if entry.disabled:
                    continue
                    
                # Create display name with entity ID and integration
                friendly_name = entry.name or entry.original_name or entry.entity_id
                entity_id = entry.entity_id
                
                # Get the integration/platform name
                platform = entry.platform if entry.platform else "unknown"
                
                # Format: "Friendly Name - entity.id (integration)"
                display_name = f"{friendly_name} - {entity_id} ({platform})"
                
                # Group by area/room - check both entity area and device area
                area_name = None
                try:
                    # First check if entity is directly assigned to an area
                    if entry.area_id:
                        area = area_reg.async_get_area(entry.area_id)
                        if area:
                            area_name = area.name
                    # If no direct entity area, check device area
                    elif entry.device_id:
                        device = dev_reg.async_get(entry.device_id)
                        if device and device.area_id:
                            area = area_reg.async_get_area(device.area_id)
                            if area:
                                area_name = area.name
                except Exception:
                    pass
                
                if area_name:
                    if area_name not in entities_by_area:
                        entities_by_area[area_name] = {}
                    entities_by_area[area_name][entity_id] = display_name
                else:
                    no_area_entities[entity_id] = display_name
            
            # Create organized entity list
            all_entities = {}
            
            # Add entities grouped by area (sorted alphabetically by area name)
            for area_name in sorted(entities_by_area.keys()):
                area_entities = entities_by_area[area_name]
                # Add area header
                area_header_key = f"_AREA_HEADER_{area_name}"
                all_entities[area_header_key] = f"🏠 {area_name} ({len(area_entities)} items) - Header Not Selectable"
                
                # Add entities in this area (sorted alphabetically)
                for entity_id in sorted(area_entities.keys()):
                    all_entities[entity_id] = f"    {area_entities[entity_id]}"
            
            # Add entities with no area at the end
            if no_area_entities:
                # Add "No Area" header
                no_area_header_key = "_AREA_HEADER_NO_AREA"
                all_entities[no_area_header_key] = f"🚫 No Area Assigned ({len(no_area_entities)} items) - Header Not Selectable"
                
                # Add entities without area (sorted alphabetically)
                for entity_id in sorted(no_area_entities.keys()):
                    all_entities[entity_id] = f"    {no_area_entities[entity_id]}"

            # Get current entities (with error handling)
            current_entities = []
            try:
                if DOMAIN in self.hass.data:
                    current_entities = self.hass.data[DOMAIN].get("entities", [])
                else:
                    # Fall back to loading from storage
                    stored_data = await async_load_entities(self.hass)
                    current_entities = stored_data.get("entities", [])
            except Exception as ex:
                _LOGGER.exception("Error loading current entities")
                current_entities = []

            # Filter out header keys for counting and validation
            selectable_entities = {k: v for k, v in all_entities.items() if not k.startswith("_AREA_HEADER_")}
            
            if not selectable_entities:
                errors["base"] = "no_entities"

            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_ENTITIES, default=current_entities
                        ): cv.multi_select(all_entities),
                    }
                ),
                errors=errors,
                description_placeholders={
                    "entity_count": str(len(selectable_entities)),
                    "selected_count": str(len(current_entities)),
                },
            )
        except Exception as ex:
            _LOGGER.exception("Error in options flow")
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema({}),
                errors={"base": "unknown"},
            )

    async def async_step_success(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the success step with restart option for options flow."""
        if user_input is not None:
            if user_input.get("restart", False):
                # Restart Home Assistant
                try:
                    await self.hass.services.async_call(
                        "homeassistant", "restart", {}, blocking=False
                    )
                except Exception as ex:
                    _LOGGER.exception("Error restarting Home Assistant")
            
            # Create the options entry
            return self.async_create_entry(title="", data={CONF_ENTITIES: self._entities})
        
        # Show success form with restart option
        return self.async_show_form(
            step_id="success",
            data_schema=vol.Schema(
                {
                    vol.Optional("restart", default=True): bool,
                }
            ),
            description_placeholders={
                "entity_count": str(len(self._entities)),
            },
        )