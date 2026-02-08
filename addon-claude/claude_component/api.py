"""API client for Claude integration."""

import logging
import aiohttp
from typing import Any, Dict, Optional
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)


class ClaudeAPI:
    """Client for communicating with Claude API."""

    def __init__(
        self,
        session: ClientSession,
        api_endpoint: str,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize the API client."""
        self.session = session
        self.api_endpoint = api_endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        self._connected = False

    async def connect(self) -> bool:
        """Test connection to the API."""
        try:
            async with self.session.get(
                f"{self.api_endpoint}/health",
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status == 200:
                    self._connected = True
                    _LOGGER.info("Successfully connected to Claude API")
                    return True
                _LOGGER.error("Failed to connect: HTTP %s", response.status)
                return False
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the API."""
        self._connected = False
        _LOGGER.info("Disconnected from Claude API")

    @property
    def is_connected(self) -> bool:
        """Return True if connected."""
        return self._connected

    async def send_message(
        self,
        message: str,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Send a message to Claude."""
        if not self._connected:
            raise RuntimeError("API not connected")

        payload = {
            "message": message,
            "context": context,
            "kwargs": kwargs,
        }

        return await self._make_request("POST", "/message", payload)

    async def execute_automation(self, automation_id: str) -> Dict[str, Any]:
        """Execute an automation."""
        if not self._connected:
            raise RuntimeError("API not connected")

        payload = {"automation_id": automation_id}
        return await self._make_request("POST", "/execute/automation", payload)

    async def execute_script(
        self,
        script_id: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a script."""
        if not self._connected:
            raise RuntimeError("API not connected")

        payload = {
            "script_id": script_id,
            "variables": variables or {},
        }
        return await self._make_request("POST", "/execute/script", payload)

    async def get_entity_state(self, entity_id: str) -> Dict[str, Any]:
        """Get entity state."""
        if not self._connected:
            raise RuntimeError("API not connected")

        return await self._make_request("GET", f"/entity/{entity_id}/state")

    async def call_service(
        self,
        service: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a Home Assistant service."""
        if not self._connected:
            raise RuntimeError("API not connected")

        payload = {
            "service": service,
            "data": data or {},
        }
        return await self._make_request("POST", "/service/call", payload)

    async def get_entities_list(self) -> Dict[str, Any]:
        """Get list of all entities."""
        if not self._connected:
            raise RuntimeError("API not connected")

        return await self._make_request("GET", "/entities")

    async def get_automations_list(self) -> Dict[str, Any]:
        """Get list of all automations."""
        if not self._connected:
            raise RuntimeError("API not connected")

        return await self._make_request("GET", "/automations")

    async def get_scripts_list(self) -> Dict[str, Any]:
        """Get list of all scripts."""
        if not self._connected:
            raise RuntimeError("API not connected")

        return await self._make_request("GET", "/scripts")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        retry: int = 0,
    ) -> Dict[str, Any]:
        """Make an API request with retry logic."""
        url = f"{self.api_endpoint}{endpoint}"

        try:
            async with self.session.request(
                method,
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                data = await response.json()

                if response.status == 200:
                    return data

                if response.status >= 500 and retry < self.max_retries:
                    _LOGGER.warning("Server error, retrying... (attempt %d)", retry + 1)
                    return await self._make_request(
                        method, endpoint, payload, retry + 1
                    )

                _LOGGER.error("API error %s: %s", response.status, data)
                return {"error": str(data), "status": response.status}

        except aiohttp.ClientError as err:
            if retry < self.max_retries:
                _LOGGER.warning("Request error, retrying... (attempt %d)", retry + 1)
                return await self._make_request(
                    method, endpoint, payload, retry + 1
                )
            _LOGGER.error("API request failed: %s", err)
            return {"error": str(err), "status": 0}
