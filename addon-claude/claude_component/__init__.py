"""Claude AI Assistant integration for Home Assistant."""

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ClaudeAPI
from .config_flow import ClaudeConfigFlow, ClaudeOptionsFlow
from .const import (
    DOMAIN,
    CONF_API_ENDPOINT,
    CONF_MODEL,
    CONF_POLLING_INTERVAL,
    CONF_TIMEOUT,
    CONF_MAX_RETRIES,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MODEL,
    MODEL_NAMES,
)
from .coordinator import ClaudeDataCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final[list[str]] = ["sensor", "switch"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Claude from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Get configuration
    api_endpoint = entry.data[CONF_API_ENDPOINT]
    model = entry.data.get(CONF_MODEL, DEFAULT_MODEL)
    polling_interval = entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)
    timeout = entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    max_retries = entry.data.get(CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES)

    # Create API client
    session = async_get_clientsession(hass)
    api = ClaudeAPI(
        session=session,
        api_endpoint=api_endpoint,
        timeout=timeout,
        max_retries=max_retries,
    )

    # Test connection
    try:
        if not await api.connect():
            _LOGGER.error("Failed to connect to Claude API")
            return False
    except Exception as err:
        _LOGGER.error("Error connecting to API: %s", err)
        return False

    # Create coordinator
    coordinator = ClaudeDataCoordinator(
        hass=hass,
        api=api,
        polling_interval=polling_interval,
    )

    # Perform first update
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and API
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "model": model,
        "model_name": MODEL_NAMES.get(model, model),
    }

    # Setup services
    await async_setup_services(hass, api)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add update listener
    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    # Setup options flow
    entry.async_on_unload(
        entry.add_update_listener(async_options_update_listener)
    )

    _LOGGER.info("Claude integration set up successfully with model: %s", MODEL_NAMES.get(model, model))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Unload services and disconnect API
        api = hass.data[DOMAIN][entry.entry_id]["api"]
        await api.disconnect()
        await async_unload_services(hass, api)

        # Remove data
        hass.data[DOMAIN].pop(entry.entry_id)

        _LOGGER.info("Claude integration unloaded")

    return unload_ok


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_options_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
