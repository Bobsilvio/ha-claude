"""Config flow for Claude integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from aiohttp import ClientSession

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ClaudeAPI
from .const import (
    DOMAIN,
    CONF_API_ENDPOINT,
    CONF_MODEL,
    DEFAULT_API_ENDPOINT,
    MODELS,
    DEFAULT_MODEL,
    MODEL_NAMES,
)

_LOGGER = logging.getLogger(__name__)


class ClaudeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Claude."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = ClaudeAPI(
                session,
                user_input[CONF_API_ENDPOINT],
                timeout=user_input.get("timeout", 30),
            )

            try:
                if await api.connect():
                    model = user_input.get(CONF_MODEL, DEFAULT_MODEL)
                    return self.async_create_entry(
                        title=f"Claude - {MODEL_NAMES.get(model, model)}",
                        data=user_input,
                    )
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error("Error: %s", err)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_ENDPOINT, default=DEFAULT_API_ENDPOINT): str,
                vol.Required(CONF_MODEL, default=DEFAULT_MODEL): vol.In(MODELS),
                vol.Optional("polling_interval", default=60): int,
                vol.Optional("enable_logging", default=True): bool,
                vol.Optional("max_retries", default=3): int,
                vol.Optional("timeout", default=30): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_import(self, import_data: Dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(user_input=import_data)


class ClaudeOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Claude."""

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MODEL,
                    default=self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL),
                ): vol.In(MODELS),
                vol.Optional(
                    "polling_interval",
                    default=self.config_entry.options.get("polling_interval", 60),
                ): int,
                vol.Optional(
                    "enable_logging",
                    default=self.config_entry.options.get("enable_logging", True),
                ): bool,
                vol.Optional(
                    "max_retries",
                    default=self.config_entry.options.get("max_retries", 3),
                ): int,
                vol.Optional(
                    "timeout",
                    default=self.config_entry.options.get("timeout", 30),
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
