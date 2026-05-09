"""Config flow for Couch Control Entity Filter integration.

The form exposes three independent selectors:

  • Areas — every entity in the picked areas is included
  • Devices — every entity belonging to the picked devices is included
  • Entities — explicit individual entity ids

The runtime filter is the union of all three resolved against the
current entity / device / area registries (see `_resolve_filter` in
`__init__.py`). Picking a whole area is a one-tap shortcut for
"include everything in this room"; the entities field stays available
for additions/exceptions that aren't covered by an area or device.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    AreaSelector,
    AreaSelectorConfig,
    DeviceSelector,
    DeviceSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
)

from .const import CONF_AREAS, CONF_DEVICES, CONF_ENTITIES, DOMAIN
from .storage import async_load_entities, async_save_entities

_LOGGER = logging.getLogger(__name__)


# Shared selector schema used by both the initial config flow and the
# options flow. Defaults are wired in per-flow because the initial
# flow always starts empty (avoids re-populating from a stale storage
# file after a previous uninstall, see related comment in
# `async_step_user`) while the options flow reads current values.
def _selector_schema(
    *,
    default_entities: list[str],
    default_areas: list[str],
    default_devices: list[str],
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(CONF_AREAS, default=default_areas): AreaSelector(
                AreaSelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_DEVICES, default=default_devices): DeviceSelector(
                DeviceSelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_ENTITIES, default=default_entities): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
        }
    )


def _filter_existing_entities(hass, entity_ids: list[str]) -> list[str]:
    """Drop entity ids that no longer exist in the registry / state machine."""
    ent_reg = er.async_get(hass)
    return [
        eid for eid in entity_ids
        if eid in ent_reg.entities or hass.states.get(eid) is not None
    ]


class CouchControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Couch Control Entity Filter."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._entities: list[str] = []
        self._areas: list[str] = []
        self._devices: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Single-instance: only one Couch Control config entry per HA.
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._entities = _filter_existing_entities(
                    self.hass, user_input.get(CONF_ENTITIES, [])
                )
                self._areas = list(user_input.get(CONF_AREAS, []))
                self._devices = list(user_input.get(CONF_DEVICES, []))

                # Persistence is deferred to `async_step_success` —
                # writing here used to leave an orphan storage file
                # if the user closed the dialog at the success step.
                return await self.async_step_success()
            except Exception:
                _LOGGER.exception("Error in config flow user step")
                errors["base"] = "unknown"

        # Fresh add: start empty. Loading storage here would re-show
        # entities from a *previous* install whose storage file still
        # exists — which historically read as "the deletion didn't
        # work". The options flow handles re-editing.
        return self.async_show_form(
            step_id="user",
            data_schema=_selector_schema(
                default_entities=[],
                default_areas=[],
                default_devices=[],
            ),
            errors=errors,
        )

    async def async_step_success(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm and optionally restart Home Assistant."""
        if user_input is not None:
            try:
                await async_save_entities(
                    self.hass,
                    {
                        CONF_ENTITIES: self._entities,
                        CONF_AREAS: self._areas,
                        CONF_DEVICES: self._devices,
                    },
                )
            except Exception:
                _LOGGER.exception("Error saving filter to storage during config flow")

            if user_input.get("restart", False):
                try:
                    await self.hass.services.async_call(
                        "homeassistant", "restart", {}, blocking=False
                    )
                except Exception:
                    _LOGGER.exception("Error restarting Home Assistant")

            return self.async_create_entry(
                title="Couch Control Entity Filter",
                data={
                    CONF_ENTITIES: self._entities,
                    CONF_AREAS: self._areas,
                    CONF_DEVICES: self._devices,
                },
            )

        return self.async_show_form(
            step_id="success",
            data_schema=vol.Schema({vol.Optional("restart", default=True): bool}),
            description_placeholders={
                "entity_count": str(len(self._entities)),
                "area_count": str(len(self._areas)),
                "device_count": str(len(self._devices)),
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
    """Handle Couch Control options (edits to an existing entry)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._entities: list[str] = []
        self._areas: list[str] = []
        self._devices: list[str] = []

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._entities = _filter_existing_entities(
                    self.hass, user_input.get(CONF_ENTITIES, [])
                )
                self._areas = list(user_input.get(CONF_AREAS, []))
                self._devices = list(user_input.get(CONF_DEVICES, []))

                await async_save_entities(
                    self.hass,
                    {
                        CONF_ENTITIES: self._entities,
                        CONF_AREAS: self._areas,
                        CONF_DEVICES: self._devices,
                    },
                )

                # Re-publish into hass.data so the runtime resolution
                # picks up changes without a restart. The actual entity
                # set is rebuilt in `async_setup_entry` /
                # `async_reload_entry`; we rebuild it here too so
                # WebSocket subscribers see the new filter immediately.
                if DOMAIN in self.hass.data:
                    from . import _resolve_filter  # local import: avoid cycle
                    resolved = _resolve_filter(
                        self.hass,
                        areas=self._areas,
                        devices=self._devices,
                        entities=self._entities,
                    )
                    self.hass.data[DOMAIN]["entities"] = list(resolved)
                    self.hass.data[DOMAIN]["areas"] = self._areas
                    self.hass.data[DOMAIN]["devices"] = self._devices

                return await self.async_step_success()
            except Exception:
                _LOGGER.exception("Error in options flow")
                errors["base"] = "unknown"

        # Load currently-stored selections so the form pre-fills with
        # what the user picked last time.
        current = await async_load_entities(self.hass)
        return self.async_show_form(
            step_id="init",
            data_schema=_selector_schema(
                default_entities=list(current.get(CONF_ENTITIES, [])),
                default_areas=list(current.get(CONF_AREAS, [])),
                default_devices=list(current.get(CONF_DEVICES, [])),
            ),
            errors=errors,
        )

    async def async_step_success(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm and optionally restart Home Assistant."""
        if user_input is not None:
            if user_input.get("restart", False):
                try:
                    await self.hass.services.async_call(
                        "homeassistant", "restart", {}, blocking=False
                    )
                except Exception:
                    _LOGGER.exception("Error restarting Home Assistant")

            return self.async_create_entry(
                title="",
                data={
                    CONF_ENTITIES: self._entities,
                    CONF_AREAS: self._areas,
                    CONF_DEVICES: self._devices,
                },
            )

        return self.async_show_form(
            step_id="success",
            data_schema=vol.Schema({vol.Optional("restart", default=True): bool}),
            description_placeholders={
                "entity_count": str(len(self._entities)),
                "area_count": str(len(self._areas)),
                "device_count": str(len(self._devices)),
            },
        )
