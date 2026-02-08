"""Services for Claude integration."""

import json
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant, ServiceCall, callback

from .api import ClaudeAPI
from .const import (
    DOMAIN,
    SERVICE_CALL_SERVICE,
    SERVICE_EXECUTE_AUTOMATION,
    SERVICE_EXECUTE_SCRIPT,
    SERVICE_GET_ENTITY_STATE,
    SERVICE_SEND_MESSAGE,
    SERVICE_CREATE_AUTOMATION,
    ATTR_MESSAGE,
    ATTR_CONTEXT,
    ATTR_AUTOMATION_ID,
    ATTR_SCRIPT_ID,
    ATTR_VARIABLES,
    ATTR_ENTITY_ID,
    ATTR_SERVICE,
    ATTR_DATA,
    ATTR_AUTOMATION_NAME,
    ATTR_TRIGGER,
    ATTR_CONDITION,
    ATTR_ACTION,
    ATTR_DESCRIPTION,
    EVENT_COMMAND_EXECUTED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant, api: ClaudeAPI) -> None:
    """Set up services for Claude."""

    async def handle_send_message(call: ServiceCall) -> None:
        """Handle send message service."""
        message = call.data.get(ATTR_MESSAGE)
        context = call.data.get(ATTR_CONTEXT)

        try:
            result = await api.send_message(message, context)
            _LOGGER.debug("Message sent: %s", result)

            hass.bus.async_fire(
                EVENT_COMMAND_EXECUTED,
                {
                    "service": SERVICE_SEND_MESSAGE,
                    "result": result,
                },
            )
        except Exception as err:
            _LOGGER.error("Error sending message: %s", err)

    async def handle_execute_automation(call: ServiceCall) -> None:
        """Handle execute automation service."""
        automation_id = call.data.get(ATTR_AUTOMATION_ID)

        try:
            result = await api.execute_automation(automation_id)
            _LOGGER.debug("Automation executed: %s", result)

            hass.bus.async_fire(
                EVENT_COMMAND_EXECUTED,
                {
                    "service": SERVICE_EXECUTE_AUTOMATION,
                    "automation_id": automation_id,
                    "result": result,
                },
            )
        except Exception as err:
            _LOGGER.error("Error executing automation: %s", err)

    async def handle_execute_script(call: ServiceCall) -> None:
        """Handle execute script service."""
        script_id = call.data.get(ATTR_SCRIPT_ID)
        variables_str = call.data.get(ATTR_VARIABLES)

        try:
            variables = {}
            if variables_str:
                if isinstance(variables_str, str):
                    variables = json.loads(variables_str)
                else:
                    variables = variables_str

            result = await api.execute_script(script_id, variables)
            _LOGGER.debug("Script executed: %s", result)

            hass.bus.async_fire(
                EVENT_COMMAND_EXECUTED,
                {
                    "service": SERVICE_EXECUTE_SCRIPT,
                    "script_id": script_id,
                    "result": result,
                },
            )
        except Exception as err:
            _LOGGER.error("Error executing script: %s", err)

    async def handle_get_entity_state(call: ServiceCall) -> None:
        """Handle get entity state service."""
        entity_id = call.data.get(ATTR_ENTITY_ID)

        try:
            result = await api.get_entity_state(entity_id)
            _LOGGER.debug("Entity state retrieved: %s", result)

            hass.bus.async_fire(
                EVENT_COMMAND_EXECUTED,
                {
                    "service": SERVICE_GET_ENTITY_STATE,
                    "entity_id": entity_id,
                    "result": result,
                },
            )
        except Exception as err:
            _LOGGER.error("Error getting entity state: %s", err)

    async def handle_call_service(call: ServiceCall) -> None:
        """Handle call service."""
        service = call.data.get(ATTR_SERVICE)
        data_str = call.data.get(ATTR_DATA)

        try:
            data = {}
            if data_str:
                if isinstance(data_str, str):
                    data = json.loads(data_str)
                else:
                    data = data_str

            result = await api.call_service(service, data)
            _LOGGER.debug("Service called: %s", result)

            hass.bus.async_fire(
                EVENT_COMMAND_EXECUTED,
                {
                    "service": SERVICE_CALL_SERVICE,
                    "called_service": service,
                    "result": result,
                },
            )
        except Exception as err:
            _LOGGER.error("Error calling service: %s", err)

    async def handle_create_automation(call: ServiceCall) -> None:
        """Handle create automation service."""
        automation_name = call.data.get(ATTR_AUTOMATION_NAME)
        description = call.data.get(ATTR_DESCRIPTION, "")
        trigger_str = call.data.get(ATTR_TRIGGER)
        condition_str = call.data.get(ATTR_CONDITION)
        action_str = call.data.get(ATTR_ACTION)

        try:
            # Parse trigger, condition, action
            trigger = {}
            condition = None
            action = []

            if trigger_str:
                if isinstance(trigger_str, str):
                    trigger = json.loads(trigger_str)
                else:
                    trigger = trigger_str

            if condition_str:
                if isinstance(condition_str, str):
                    condition = json.loads(condition_str)
                else:
                    condition = condition_str

            if action_str:
                if isinstance(action_str, str):
                    action = json.loads(action_str)
                    if not isinstance(action, list):
                        action = [action]
                else:
                    action = action_str if isinstance(action_str, list) else [action_str]

            # Create automation ID from name
            automation_id = f"automation.{automation_name.lower().replace(' ', '_')}"

            # Build automation YAML
            automation_config = {
                "id": automation_id,
                "alias": automation_name,
                "description": description,
                "trigger": trigger,
            }

            if condition:
                automation_config["condition"] = condition

            automation_config["action"] = action

            # Save to automations.yaml
            automations_path = hass.config.path("automations.yaml")
            _LOGGER.info(f"Creating automation: {automation_id}")

            # Load existing automations
            try:
                import yaml

                with open(automations_path, 'r') as f:
                    automations = yaml.safe_load(f) or []
            except FileNotFoundError:
                automations = []

            # Add new automation
            automations.append(automation_config)

            # Save back
            with open(automations_path, 'w') as f:
                yaml.dump(automations, f, default_flow_style=False)

            _LOGGER.debug("Automation created: %s", automation_config)

            # Reload automations
            await hass.services.async_call("automation", "reload")

            hass.bus.async_fire(
                EVENT_COMMAND_EXECUTED,
                {
                    "service": SERVICE_CREATE_AUTOMATION,
                    "automation_id": automation_id,
                    "automation_name": automation_name,
                    "result": "success",
                },
            )
        except Exception as err:
            _LOGGER.error("Error creating automation: %s", err)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_MESSAGE,
        handle_send_message,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTE_AUTOMATION,
        handle_execute_automation,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTE_SCRIPT,
        handle_execute_script,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_ENTITY_STATE,
        handle_get_entity_state,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CALL_SERVICE,
        handle_call_service,
    )

    _LOGGER.debug("Services registered successfully")


async def async_unload_services(hass: HomeAssistant, api: ClaudeAPI) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_SEND_MESSAGE)
    hass.services.async_remove(DOMAIN, SERVICE_EXECUTE_AUTOMATION)
    hass.services.async_remove(DOMAIN, SERVICE_EXECUTE_SCRIPT)
    hass.services.async_remove(DOMAIN, SERVICE_GET_ENTITY_STATE)
    hass.services.async_remove(DOMAIN, SERVICE_CALL_SERVICE)
    _LOGGER.debug("Services unloaded")
