"""Config flow for Couch Control Entity Filter integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er, area_registry as ar, config_validation as cv
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
                self._entities = user_input.get(CONF_ENTITIES, [])
                
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
            # Get all available entities
            ent_reg = er.async_get(self.hass)
            all_entities = {}
            
            for entry in ent_reg.entities.values():
                if entry.disabled:
                    continue
                    
                # Create display name with entity ID and integration
                friendly_name = entry.name or entry.original_name or entry.entity_id
                entity_id = entry.entity_id
                domain = entity_id.split(".")[0]
                
                # Get the integration/platform name
                platform = entry.platform if entry.platform else "unknown"
                
                # Format: "Friendly Name - entity.id (integration)"
                display_name = f"{friendly_name} - {entity_id} ({platform})"
                
                all_entities[entry.entity_id] = display_name

            # Load existing selections (with error handling)
            try:
                existing_data = await async_load_entities(self.hass)
                existing_entities = existing_data.get("entities", [])
            except Exception as ex:
                _LOGGER.exception("Error loading existing entities")
                existing_entities = []

            if not all_entities:
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
                    "entity_count": str(len(all_entities)),
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
            # Get all available entities
            ent_reg = er.async_get(self.hass)
            all_entities = {}
            
            for entry in ent_reg.entities.values():
                if entry.disabled:
                    continue
                    
                # Create display name with entity ID and integration
                friendly_name = entry.name or entry.original_name or entry.entity_id
                entity_id = entry.entity_id
                domain = entity_id.split(".")[0]
                
                # Get the integration/platform name
                platform = entry.platform if entry.platform else "unknown"
                
                # Add area if available (with error handling)
                area_prefix = ""
                try:
                    if entry.area_id:
                        area_reg = ar.async_get(self.hass)
                        area = area_reg.async_get_area(entry.area_id)
                        if area:
                            area_prefix = f"{area.name} - "
                except Exception:
                    # If area lookup fails, just continue without area
                    pass
                
                # Format: "[Area - ]Friendly Name - entity.id (integration)"
                display_name = f"{area_prefix}{friendly_name} - {entity_id} ({platform})"
                all_entities[entry.entity_id] = display_name

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

            if not all_entities:
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
                    "entity_count": str(len(all_entities)),
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