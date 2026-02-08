"""Switch platform for Claude integration."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ClaudeAPI
from .coordinator import ClaudeDataCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches for Claude."""

    api: ClaudeAPI = hass.data[DOMAIN][config_entry.entry_id]["api"]
    coordinator: ClaudeDataCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities = [
        ClaudeConnectionSwitch(coordinator, api),
    ]

    async_add_entities(entities)


class ClaudeConnectionSwitch(CoordinatorEntity, SwitchEntity):
    """Switch for Claude connection."""

    _attr_name = "Claude Connection"
    _attr_unique_id = "claude_connection"
    _attr_icon = "mdi:cloud-check"

    def __init__(
        self,
        coordinator: ClaudeDataCoordinator,
        api: ClaudeAPI,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._api.is_connected

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            await self._api.connect()
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Error connecting: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            await self._api.disconnect()
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Error disconnecting: %s", err)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True
