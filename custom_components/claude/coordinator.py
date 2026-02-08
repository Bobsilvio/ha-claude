"""Data coordinator for Claude integration."""

import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ClaudeAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)


class ClaudeDataCoordinator(DataUpdateCoordinator):
    """Data coordinator for Claude."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ClaudeAPI,
        polling_interval: int = 60,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=polling_interval),
        )

        self.api = api
        self._entities_cache: Dict[str, Any] = {}
        self._automations_cache: Dict[str, Any] = {}
        self._scripts_cache: Dict[str, Any] = {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data from API."""
        try:
            if not self.api.is_connected:
                raise UpdateFailed("API not connected")

            # Fetch all data
            entities = await self.api.get_entities_list()
            automations = await self.api.get_automations_list()
            scripts = await self.api.get_scripts_list()

            self._entities_cache = entities.get("entities", {})
            self._automations_cache = automations.get("automations", {})
            self._scripts_cache = scripts.get("scripts", {})

            return {
                "entities": self._entities_cache,
                "automations": self._automations_cache,
                "scripts": self._scripts_cache,
                "status": "connected",
            }

        except Exception as err:
            _LOGGER.error("Error updating data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    @property
    def entities(self) -> Dict[str, Any]:
        """Get cached entities."""
        return self._entities_cache

    @property
    def automations(self) -> Dict[str, Any]:
        """Get cached automations."""
        return self._automations_cache

    @property
    def scripts(self) -> Dict[str, Any]:
        """Get cached scripts."""
        return self._scripts_cache
