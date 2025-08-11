"""Config flow for Couch Control integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import DOMAIN, CONF_SELECTED_ENTITIES

_LOGGER = logging.getLogger(__name__)

class CouchControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Couch Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="Couch Control",
                data={},
                options={CONF_SELECTED_ENTITIES: user_input.get(CONF_SELECTED_ENTITIES, [])},
            )

        # Get all entities for selection
        entity_registry = async_get_entity_registry(self.hass)
        entities = []
        
        for entity in entity_registry.entities.values():
            if entity.disabled_by is None:  # Only include enabled entities
                entities.append(entity.entity_id)
        
        entities.sort()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(CONF_SELECTED_ENTITIES, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                        filter=selector.EntityFilterSelectorConfig(
                            domain=["light", "switch", "sensor", "binary_sensor", "media_player", "climate", "weather", "scene", "calendar"]
                        )
                    )
                ),
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Couch Control."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_entities = self.config_entry.options.get(CONF_SELECTED_ENTITIES, [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_SELECTED_ENTITIES, default=current_entities): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                        filter=selector.EntityFilterSelectorConfig(
                            domain=["light", "switch", "sensor", "binary_sensor", "media_player", "climate", "weather", "scene", "calendar"]
                        )
                    )
                ),
            }),
        )