"""MCP Custom Authentication Headers Support.

Extends the Model Context Protocol implementation with custom authentication
headers, allowing secure communication with restricted MCP servers.

Features:
- Per-server API key management
- Custom header injection
- Request signing (optional)
- Credential rotation
"""

import logging
import json
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import hashlib
import time

logger = logging.getLogger(__name__)


@dataclass
class MCPAuthConfig:
    """Authentication configuration for an MCP server."""
    server_name: str
    server_url: str
    auth_type: str = "api_key"  # api_key, bearer, basic, custom
    credentials: Dict[str, str] = field(default_factory=dict)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    require_signature: bool = False
    signature_secret: Optional[str] = None


class MCPAuthHeaderManager:
    """Manages custom authentication headers for MCP servers."""

    def __init__(self):
        """Initialize MCP auth manager."""
        self.configs: Dict[str, MCPAuthConfig] = {}
        self.request_counter = 0

    def register_server(
        self,
        server_name: str,
        server_url: str,
        auth_type: str = "api_key",
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> MCPAuthConfig:
        """Register an MCP server with authentication.
        
        Args:
            server_name: Unique server identifier
            server_url: Server URL
            auth_type: "api_key", "bearer", "basic", or "custom"
            api_key: API key (for api_key/bearer types)
            custom_headers: Additional custom headers
            
        Returns:
            MCPAuthConfig object
        """
        config = MCPAuthConfig(
            server_name=server_name,
            server_url=server_url,
            auth_type=auth_type,
            custom_headers=custom_headers or {},
        )

        if auth_type == "api_key":
            if not api_key:
                raise ValueError(f"api_key required for auth_type='api_key'")
            config.credentials["api_key"] = api_key

        elif auth_type == "bearer":
            if not api_key:
                raise ValueError(f"api_key required for auth_type='bearer'")
            config.credentials["token"] = api_key

        elif auth_type == "basic":
            if not api_key:
                raise ValueError(f"api_key required for auth_type='basic'")
            # Assuming format is "username:password"
            config.credentials["basic_auth"] = api_key

        self.configs[server_name] = config
        logger.info(
            f"MCPAuthHeaderManager: registered server '{server_name}' with auth_type='{auth_type}'"
        )

        return config

    def get_headers_for_server(self, server_name: str) -> Dict[str, str]:
        """Get authentication headers for a server.
        
        Args:
            server_name: Server identifier
            
        Returns:
            Dictionary of headers to include in requests
            
        Raises:
            KeyError: If server not registered
        """
        if server_name not in self.configs:
            raise KeyError(f"MCP server '{server_name}' not registered")

        config = self.configs[server_name]
        headers = dict(config.custom_headers)  # Start with custom headers

        if config.auth_type == "api_key":
            # Common API key header names
            headers["X-API-Key"] = config.credentials["api_key"]

        elif config.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {config.credentials['token']}"

        elif config.auth_type == "basic":
            headers["Authorization"] = f"Basic {config.credentials['basic_auth']}"

        if config.require_signature:
            # Add request signature header
            signature = self._generate_signature(config)
            headers["X-Request-Signature"] = signature
            headers["X-Request-Timestamp"] = str(int(time.time()))
            headers["X-Request-Nonce"] = self._generate_nonce()

        return headers

    def _generate_signature(self, config: MCPAuthConfig) -> str:
        """Generate HMAC signature for request.
        
        Args:
            config: MCPAuthConfig with signature_secret set
            
        Returns:
            Hex-encoded HMAC signature
        """
        if not config.signature_secret:
            raise ValueError("signature_secret not set for signing")

        self.request_counter += 1
        message = f"{config.server_name}:{self.request_counter}:{int(time.time())}"

        import hmac
        signature = hmac.new(
            config.signature_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return signature

    def _generate_nonce(self) -> str:
        """Generate unique nonce for request."""
        import secrets
        return secrets.token_hex(8)

    def inject_auth_headers(
        self,
        server_name: str,
        request_dict: Dict[str, Any],
        headers_key: str = "headers",
    ) -> Dict[str, Any]:
        """Inject authentication headers into a request dict.
        
        Args:
            server_name: Server identifier
            request_dict: Request dictionary to modify
            headers_key: Key where headers should be stored
            
        Returns:
            Modified request_dict
        """
        auth_headers = self.get_headers_for_server(server_name)

        if headers_key not in request_dict:
            request_dict[headers_key] = {}

        request_dict[headers_key].update(auth_headers)
        logger.debug(
            f"MCPAuthHeaderManager: injected {len(auth_headers)} auth headers "
            f"for server '{server_name}'"
        )

        return request_dict

    def rotate_credential(
        self,
        server_name: str,
        new_api_key: str,
    ):
        """Rotate API key for a server.
        
        Args:
            server_name: Server identifier
            new_api_key: New API key value
        """
        if server_name not in self.configs:
            raise KeyError(f"MCP server '{server_name}' not registered")

        config = self.configs[server_name]
        old_key = config.credentials.get("api_key", "***hidden***")

        if config.auth_type == "api_key":
            config.credentials["api_key"] = new_api_key
        elif config.auth_type == "bearer":
            config.credentials["token"] = new_api_key
        elif config.auth_type == "basic":
            config.credentials["basic_auth"] = new_api_key

        logger.info(
            f"MCPAuthHeaderManager: rotated credential for server '{server_name}' from '{old_key[:10]}...' to '{new_api_key[:10]}...'"
        )

    def get_server_config(self, server_name: str) -> MCPAuthConfig:
        """Get auth config for a server.
        
        Args:
            server_name: Server identifier
            
        Returns:
            MCPAuthConfig object
        """
        if server_name not in self.configs:
            raise KeyError(f"MCP server '{server_name}' not registered")
        return self.configs[server_name]

    def list_registered_servers(self) -> Dict[str, str]:
        """List all registered MCP servers.
        
        Returns:
            Dict of {server_name: server_url}
        """
        return {name: config.server_url for name, config in self.configs.items()}


# Global instance
_auth_manager: Optional[MCPAuthHeaderManager] = None


def get_mcp_auth_manager() -> MCPAuthHeaderManager:
    """Get or create the global MCP auth manager."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = MCPAuthHeaderManager()
    return _auth_manager


def setup_mcp_auth_from_config(
    config_dict: Dict[str, Any],
    use_global: bool = True,
) -> MCPAuthHeaderManager:
    """Setup MCP authentication from configuration dict.
    
    Expected config format:
    ```yaml
    mcp_servers:
      - name: "my_server"
        url: "http://localhost:3000"
        auth_type: "api_key"
        api_key: "${MCP_SERVER_KEY}"
        custom_headers:
          X-Custom-Header: "value"
    ```
    
    Args:
        config_dict: Configuration dictionary
        use_global: Use global manager (True for production, False for testing)
        
    Returns:
        Configured MCPAuthHeaderManager
    """
    manager = get_mcp_auth_manager() if use_global else MCPAuthHeaderManager()
    mcp_configs = config_dict.get("mcp_servers", [])

    if not isinstance(mcp_configs, list):
        mcp_configs = [mcp_configs]

    for server_config in mcp_configs:
        name = server_config.get("name")
        url = server_config.get("url")
        auth_type = server_config.get("auth_type", "api_key")
        api_key = server_config.get("api_key")
        custom_headers = server_config.get("custom_headers", {})

        if not name or not url:
            logger.warning(f"Skipping MCP server config missing name or url: {server_config}")
            continue

        try:
            manager.register_server(
                server_name=name,
                server_url=url,
                auth_type=auth_type,
                api_key=api_key,
                custom_headers=custom_headers,
            )
            logger.info(f"Registered MCP server: {name} ({url})")
        except Exception as e:
            logger.error(f"Failed to register MCP server '{name}': {e}")

    return manager
