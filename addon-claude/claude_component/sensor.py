"""Sensor platform for Claude integration."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ClaudeDataCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for Claude."""

    coordinator: ClaudeDataCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities = [
        ClaudeStatusSensor(coordinator),
        ClaudeEntitiesCountSensor(coordinator),
        ClaudeAutomationsCountSensor(coordinator),
        ClaudeScriptsCountSensor(coordinator),
    ]

    async_add_entities(entities)


class ClaudeStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor for Claude status."""

    _attr_name = "Claude Status"
    _attr_unique_id = "claude_status"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator: ClaudeDataCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_options = ["connected", "disconnected", "error"]

    @property
    def native_value(self) -> str:
        """Return the status."""
        if self.coordinator.last_update_success:
            return "connected"
        return "disconnected"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True


class ClaudeEntitiesCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor for entities count."""

    _attr_name = "Claude Entities Count"
    _attr_unique_id = "claude_entities_count"
    _attr_device_class = SensorDeviceClass.ENUM

    @property
    def native_value(self) -> int | None:
        """Return the count."""
        if self.coordinator.data:
            return len(self.coordinator.entities)
        return None


class ClaudeAutomationsCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor for automations count."""

    _attr_name = "Claude Automations Count"
    _attr_unique_id = "claude_automations_count"
    _attr_device_class = SensorDeviceClass.ENUM

    @property
    def native_value(self) -> int | None:
        """Return the count."""
        if self.coordinator.data:
            return len(self.coordinator.automations)
        return None


class ClaudeScriptsCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor for scripts count."""

    _attr_name = "Claude Scripts Count"
    _attr_unique_id = "claude_scripts_count"
    _attr_device_class = SensorDeviceClass.ENUM

    @property
    def native_value(self) -> int | None:
        """Return the count."""
        if self.coordinator.data:
            return len(self.coordinator.scripts)
        return None
