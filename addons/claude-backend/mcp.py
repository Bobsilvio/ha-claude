"""Model Context Protocol (MCP) support for external tool servers.

Supports both stdio (local) and HTTP (remote) transport modes.
Auto-discovers tools from MCP servers and registers them with the agent.

Reference: https://modelcontextprotocol.io/
"""

import json
import logging
import subprocess
import threading
import time
import requests
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Official MCP SDK (pip install mcp) ────────────────────────────────────────
try:
    from mcp import ClientSession, StdioServerParameters   # type: ignore
    from mcp.client.stdio import stdio_client              # type: ignore
    _MCP_SDK_AVAILABLE = True
    logger.debug("Official mcp SDK found")
except ImportError:
    _MCP_SDK_AVAILABLE = False
    logger.debug("Official mcp SDK not installed; using built-in STDIO transport")


class _OfficialMCPStdioClient:
    """
    Wrapper sync-over-async per il pacchetto ufficiale `mcp` (pip install mcp).

    Mantiene la connessione al processo STDIO aperta in un loop asyncio
    dedicato (thread daemon), espone un'interfaccia completamente sincrona
    compatibile con il resto del codice Flask.
    """

    def __init__(self, command: str, args: list, env: Optional[dict] = None):
        import asyncio
        import os as _os
        self._cmd = command
        self._args = args or []
        self._env = {**_os.environ, **(env or {})}
        self._tools: List[Dict] = []
        self._session = None
        self._exit_stack = None
        # Loop asyncio dedicato in thread daemon
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        import asyncio
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _submit(self, coro, timeout: float = 30.0):
        """Esegue una coroutine nel loop background, bloccando fino al risultato."""
        import concurrent.futures
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout=timeout)

    # ── Public sync interface ────────────────────────────────────────────────

    def connect(self) -> bool:
        """Connette al server MCP via stdio e scopre i tool."""
        return self._submit(self._async_connect(), timeout=15.0)

    @property
    def discovered_tools(self) -> List[Dict]:
        return self._tools

    def call_tool(self, name: str, arguments: Dict) -> str:
        """Chiama un tool, restituisce il risultato come stringa."""
        return self._submit(self._async_call_tool(name, arguments), timeout=30.0)

    def disconnect(self) -> None:
        if self._exit_stack:
            try:
                self._submit(self._exit_stack.aclose(), timeout=5.0)
            except Exception:
                pass
        try:
            self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:
            pass

    # ── Async internals ──────────────────────────────────────────────────────

    async def _async_connect(self) -> bool:
        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        params = StdioServerParameters(
            command=self._cmd, args=self._args, env=self._env
        )
        read, write = await self._exit_stack.enter_async_context(stdio_client(params))
        session = ClientSession(read, write)
        self._session = await self._exit_stack.enter_async_context(session)
        await self._session.initialize()
        response = await self._session.list_tools()
        self._tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "inputSchema": dict(t.inputSchema) if t.inputSchema else {},
            }
            for t in response.tools
        ]
        return True

    async def _async_call_tool(self, name: str, arguments: Dict) -> str:
        result = await self._session.call_tool(name, arguments)
        parts = [c.text if hasattr(c, "text") else str(c) for c in (result.content or [])]
        return "\n".join(parts) or "{}"


class MCPRetryHandler:
    """Handles retry logic with exponential backoff for MCP operations."""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 0.5, max_delay: float = 10.0):
        """Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None on failure
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate exponential backoff: 0.5s, 1s, 2s, up to max_delay
                    delay = min(self.initial_delay * (2 ** attempt), self.max_delay)
                    logger.debug(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed: {e}")
        
        raise last_exception


# Global retry handler
_retry_handler = MCPRetryHandler(max_retries=3, initial_delay=0.5, max_delay=10.0)


class MCPSchemaValidator:
    """Validates MCP tool arguments against JSON Schema."""
    
    @staticmethod
    def validate(arguments: Dict, schema: Dict) -> tuple[bool, Optional[str]]:
        """Validate arguments against JSON schema.
        
        Args:
            arguments: Arguments dictionary to validate
            schema: JSON schema to validate against
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not schema:
            return True, None
        
        try:
            # Extract schema properties
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            # Check required fields
            for field in required:
                if field not in arguments:
                    return False, f"Missing required field: {field}"
            
            # Check field types
            for field, value in arguments.items():
                if field in properties:
                    prop_schema = properties[field]
                    prop_type = prop_schema.get("type", "")
                    
                    # Type checking
                    type_map = {
                        "string": str,
                        "number": (int, float),
                        "integer": int,
                        "boolean": bool,
                        "array": list,
                        "object": dict,
                    }
                    
                    expected_type = type_map.get(prop_type)
                    if expected_type and not isinstance(value, expected_type):
                        return False, f"Field '{field}' must be of type {prop_type}, got {type(value).__name__}"
                    
                    # Enum validation
                    enum_values = prop_schema.get("enum", [])
                    if enum_values and value not in enum_values:
                        return False, f"Field '{field}' must be one of {enum_values}, got {value}"
                    
                    # Number range validation
                    if prop_type in ("number", "integer"):
                        minimum = prop_schema.get("minimum")
                        maximum = prop_schema.get("maximum")
                        if minimum is not None and value < minimum:
                            return False, f"Field '{field}' must be >= {minimum}, got {value}"
                        if maximum is not None and value > maximum:
                            return False, f"Field '{field}' must be <= {maximum}, got {value}"
                    
                    # String length validation
                    if prop_type == "string":
                        min_length = prop_schema.get("minLength")
                        max_length = prop_schema.get("maxLength")
                        if min_length is not None and len(value) < min_length:
                            return False, f"Field '{field}' must have at least {min_length} characters"
                        if max_length is not None and len(value) > max_length:
                            return False, f"Field '{field}' must have at most {max_length} characters"
            
            return True, None
        except Exception as e:
            logger.warning(f"Schema validation warning: {e}")
            return True, None  # Don't fail on validation errors, just warn


class MCPServer:
    """Represents a single MCP server connection."""
    
    TRANSPORT_STDIO = "stdio"
    TRANSPORT_HTTP = "http"
    
    def __init__(self, name: str, transport_type: str, config: Dict[str, Any]):
        """Initialize MCP server.
        
        Args:
            name: Server name (e.g., 'filesystem')
            transport_type: Either 'stdio' or 'http'
            config: Server configuration dict
                   For stdio: {command, args, env}
                   For HTTP: {url, headers}
        """
        self.name = name
        self.transport_type = transport_type
        self.config = config
        self.process = None
        self.session_id = None
        self.tools: Dict[str, Dict] = {}  # tool_name -> {description, inputSchema}
        self.resources: Dict[str, Dict] = {}  # resource_uri -> metadata
        self._connected = False
        self._call_lock = threading.Lock()  # serialise concurrent tool calls per server
        self._official_client: Optional[_OfficialMCPStdioClient] = None  # official SDK
        
    def connect(self) -> bool:
        """Connect to MCP server.
        
        Returns:
            True if connection successful
        """
        try:
            if self.transport_type == self.TRANSPORT_STDIO:
                return self._connect_stdio()
            elif self.transport_type == self.TRANSPORT_HTTP:
                return self._connect_http()
            else:
                logger.error(f"MCP {self.name}: Unknown transport {self.transport_type}")
                return False
        except Exception as e:
            logger.error(f"MCP {self.name}: Connection failed: {e}")
            return False
    
    def _connect_stdio(self) -> bool:
        """Connect via stdio — uses official mcp SDK when available, else built-in."""
        cmd = self.config.get("command")
        args = self.config.get("args", [])
        env = self.config.get("env", {})

        if not cmd:
            logger.error(f"MCP {self.name}: Missing 'command' in stdio config")
            return False

        # ── Try official mcp SDK first ────────────────────────────────────────
        if _MCP_SDK_AVAILABLE:
            try:
                client = _OfficialMCPStdioClient(cmd, args, env)
                ok = client.connect()
                if ok:
                    self._official_client = client
                    for tool in client.discovered_tools:
                        self.tools[tool["name"]] = {
                            "description": tool["description"],
                            "inputSchema": tool["inputSchema"],
                        }
                    self._connected = True
                    logger.info(
                        f"MCP {self.name}: Connected via official mcp SDK "
                        f"({len(self.tools)} tools)"
                    )
                    return True
            except Exception as e:
                logger.warning(
                    f"MCP {self.name}: Official SDK failed ({e}), "
                    f"falling back to built-in transport"
                )
                self._official_client = None

        # ── Fallback: built-in subprocess transport ───────────────────────────
        try:
            full_cmd = [cmd] + args
            logger.debug(f"MCP {self.name}: Starting stdio process: {full_cmd}")
            import os as _os
            self.process = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**dict(_os.environ), **env},
            )
            self._connected = True
            logger.info(
                f"MCP {self.name}: Connected via built-in transport (PID: {self.process.pid})"
            )
            return self._discover_tools_stdio()
        except Exception as e:
            logger.error(f"MCP {self.name}: Stdio connection error: {e}")
            return False
    
    def _connect_http(self) -> bool:
        """Connect via HTTP (remote MCP server, JSON-RPC over HTTP)."""
        try:
            url = self.config.get("url")
            headers = self.config.get("headers", {})

            if not url:
                logger.error(f"MCP {self.name}: Missing 'url' in HTTP config")
                return False

            self._connected = True
            logger.info(f"MCP {self.name}: Connected via HTTP ({url})")

            # Discover tools
            return self._discover_tools_http()
        except Exception as e:
            logger.error(f"MCP {self.name}: HTTP connection error: {e}")
            return False
    
    def _discover_tools_stdio(self) -> bool:
        """Discover available tools from stdio server."""
        try:
            # Send initialize request
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"}
            }
            
            response = self._send_request_stdio(init_msg)
            if not response:
                logger.warning(f"MCP {self.name}: Initialize failed")
                return False
            
            # Send list_tools request
            tools_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            response = self._send_request_stdio(tools_msg)
            if response and "result" in response:
                tools_list = response["result"].get("tools", [])
                for tool in tools_list:
                    self.tools[tool["name"]] = {
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("inputSchema", {})
                    }
                
                logger.info(f"MCP {self.name}: Discovered {len(self.tools)} tools")
                return True
            
            return False
        except Exception as e:
            logger.error(f"MCP {self.name}: Tool discovery failed: {e}")
            return False
    
    def _discover_tools_http(self) -> bool:
        """Discover available tools from HTTP server (standard MCP JSON-RPC)."""
        try:
            url = self.config.get("url").rstrip("/")
            headers = {"Content-Type": "application/json", **self.config.get("headers", {})}

            # MCP standard: initialize first
            init_payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2024-11-05"}}
            requests.post(url, json=init_payload, headers=headers, timeout=5)

            # Then list tools via JSON-RPC POST
            tools_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            resp = requests.post(url, json=tools_payload, headers=headers, timeout=5)

            if resp.status_code == 200:
                data = resp.json()
                tools_list = data.get("result", {}).get("tools", [])

                for tool in tools_list:
                    self.tools[tool["name"]] = {
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("inputSchema", {})
                    }

                logger.info(f"MCP {self.name}: Discovered {len(self.tools)} tools via HTTP")
                return True
            else:
                logger.warning(f"MCP {self.name}: HTTP tools/list returned {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"MCP {self.name}: HTTP tool discovery failed: {e}")
            return False
    
    def _send_request_stdio(self, request: Dict) -> Optional[Dict]:
        """Send request via stdio and get response."""
        try:
            if not self.process:
                return None
            
            # Send request
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            
            # Read response (with timeout)
            import select
            if select.select([self.process.stdout], [], [], 5)[0]:
                response_line = self.process.stdout.readline()
                return json.loads(response_line)
            else:
                logger.warning(f"MCP {self.name}: stdio read timeout")
                return None
        except Exception as e:
            logger.error(f"MCP {self.name}: stdio request failed: {e}")
            return None
    
    def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments dict
            
        Returns:
            Tool result as JSON string
        """
        with self._call_lock:  # serialise: stdio process is not thread-safe
            return self._call_tool_locked(tool_name, arguments)

    def _call_tool_locked(self, tool_name: str, arguments: Dict) -> str:
        """Internal call_tool implementation (must be called with _call_lock held)."""
        try:
            if tool_name not in self.tools:
                return json.dumps({"error": f"Tool '{tool_name}' not found on {self.name}"})
            
            if self.transport_type == self.TRANSPORT_STDIO:
                # Usa il client ufficiale se disponibile (più robusto)
                if self._official_client:
                    return self._official_client.call_tool(tool_name, arguments)
                # Fallback: built-in JSON-RPC su subprocess
                tool_msg = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                }
                response = self._send_request_stdio(tool_msg)
                if response and "result" in response:
                    return json.dumps(response["result"])
                else:
                    return json.dumps({"error": "Tool call failed"})
            
            elif self.transport_type == self.TRANSPORT_HTTP:
                # Standard MCP HTTP: JSON-RPC POST to server root
                url = self.config.get("url").rstrip("/")
                headers = {"Content-Type": "application/json", **self.config.get("headers", {})}
                payload = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments}
                }
                resp = requests.post(url, json=payload, headers=headers, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if "result" in data:
                        return json.dumps(data["result"])
                    elif "error" in data:
                        return json.dumps({"error": data["error"].get("message", "Unknown error")})
                return json.dumps({"error": f"HTTP {resp.status_code}"})
            
            else:
                return json.dumps({"error": f"Unknown transport: {self.transport_type}"})
        except Exception as e:
            logger.error(f"MCP {self.name}: Tool call error: {e}")
            return json.dumps({"error": str(e)})
    
    def disconnect(self) -> None:
        """Disconnect from MCP server."""
        try:
            if self._official_client:
                self._official_client.disconnect()
                self._official_client = None
            elif self.process:
                self.process.terminate()
                self.process.wait(timeout=2)
                logger.debug(f"MCP {self.name}: Process terminated")
        except Exception as e:
            logger.warning(f"MCP {self.name}: Disconnect error: {e}")
        finally:
            self._connected = False
    
    def is_connected(self) -> bool:
        """Check if server is connected."""
        if self.transport_type == self.TRANSPORT_STDIO:
            if self._official_client:
                return self._connected
            return self._connected and self.process is not None and self.process.poll() is None
        return self._connected


class MCPManager:
    """Manages multiple MCP server connections."""
    
    def __init__(self):
        """Initialize MCP manager."""
        self.servers: Dict[str, MCPServer] = {}
        self._lock = threading.Lock()
    
    def add_server(self, name: str, transport_type: str, config: Dict[str, Any]) -> bool:
        """Add and connect to an MCP server.
        
        Args:
            name: Server name
            transport_type: 'stdio' or 'http'
            config: Transport-specific configuration
            
        Returns:
            True if server connected successfully
        """
        try:
            with self._lock:
                if name in self.servers:
                    logger.warning(f"MCP: Server '{name}' already registered, reconnecting...")
                    self.servers[name].disconnect()
                
                server = MCPServer(name, transport_type, config)
                if server.connect():
                    self.servers[name] = server
                    logger.info(f"MCP: Registered server '{name}' with {len(server.tools)} tools")
                    return True
                else:
                    logger.error(f"MCP: Failed to connect to server '{name}'")
                    return False
        except Exception as e:
            logger.error(f"MCP: Error adding server '{name}': {e}")
            return False
    
    def get_all_tools(self) -> Dict[str, Dict]:
        """Get all available tools from all servers.
        
        Returns:
            Dict mapping tool_name -> {server, description, inputSchema}
        """
        all_tools = {}
        with self._lock:
            for server_name, server in self.servers.items():
                if server.is_connected():
                    for tool_name, tool_info in server.tools.items():
                        # Prefix tool name with server name to avoid conflicts
                        prefixed_name = f"mcp_{server_name}_{tool_name}"
                        all_tools[prefixed_name] = {
                            "server": server_name,
                            "tool_name": tool_name,
                            "description": tool_info["description"],
                            "inputSchema": tool_info["inputSchema"]
                        }
        return all_tools
    
    def call_tool(self, prefixed_tool_name: str, arguments: Dict, max_retries: int = 2) -> str:
        """Call a tool on an MCP server with retry logic.
        
        Args:
            prefixed_tool_name: Tool name with 'mcp_server_toolname' format
            arguments: Tool arguments
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tool result as JSON string
        """
        try:
            # Parse prefixed name: mcp_servername_toolname
            parts = prefixed_tool_name.split("_", 2)
            if len(parts) != 3 or parts[0] != "mcp":
                return json.dumps({"error": f"Invalid tool name format: {prefixed_tool_name}"})
            
            server_name = parts[1]
            tool_name = parts[2]
            
            with self._lock:
                if server_name not in self.servers:
                    return json.dumps({"error": f"MCP server '{server_name}' not found"})
                
                server = self.servers[server_name]
                
                # Validate arguments against tool schema
                if tool_name in server.tools:
                    tool_info = server.tools[tool_name]
                    input_schema = tool_info.get("inputSchema", {})
                    
                    is_valid, error_msg = MCPSchemaValidator.validate(arguments, input_schema)
                    if not is_valid:
                        logger.warning(f"MCP: Schema validation failed for {prefixed_tool_name}: {error_msg}")
                        return json.dumps({"error": f"Argument validation failed: {error_msg}"})
            
            # Execute with retry logic
            start_time = time.time()
            for attempt in range(max_retries + 1):
                try:
                    result = server.call_tool(tool_name, arguments)
                    elapsed = time.time() - start_time
                    
                    # If result contains error, still return it (tool-specific error, not transport error)
                    try:
                        result_obj = json.loads(result)
                        if result_obj.get("error") and attempt < max_retries:
                            logger.debug(f"MCP: Tool returned error, retrying {attempt + 1}/{max_retries + 1}")
                            time.sleep(0.5 * (2 ** attempt))
                            continue
                    except (json.JSONDecodeError, TypeError):
                        pass
                    
                    logger.debug(f"MCP: Tool call succeeded in {elapsed:.2f}s (attempt {attempt + 1})")
                    return result
                    
                except Exception as e:
                    if attempt < max_retries:
                        delay = 0.5 * (2 ** attempt)
                        logger.warning(f"MCP: Tool call failed, retrying in {delay}s... ({attempt + 1}/{max_retries + 1}): {e}")
                        time.sleep(delay)
                    else:
                        elapsed = time.time() - start_time
                        logger.error(f"MCP: Tool call failed after {elapsed:.2f}s and {max_retries + 1} attempts: {e}")
                        return json.dumps({"error": f"Tool call failed: {str(e)}"})
        
        except Exception as e:
            logger.error(f"MCP: Tool routing error: {e}")
            return json.dumps({"error": str(e)})
    
    def disconnect_all(self) -> None:
        """Disconnect all servers."""
        with self._lock:
            for server_name, server in list(self.servers.items()):
                logger.debug(f"MCP: Disconnecting '{server_name}'...")
                server.disconnect()
            self.servers.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get manager statistics.
        
        Returns:
            Dict with connection stats
        """
        with self._lock:
            connected = sum(1 for s in self.servers.values() if s.is_connected())
            total_tools = sum(len(s.tools) for s in self.servers.values())
            
            return {
                "servers_configured": len(self.servers),
                "servers_connected": connected,
                "total_tools": total_tools,
                "servers": {
                    name: {
                        "connected": server.is_connected(),
                        "transport": server.transport_type,
                        "tools": len(server.tools),
                    }
                    for name, server in self.servers.items()
                }
            }


# Global MCP manager instance
_mcp_manager = MCPManager()


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager.
    
    Returns:
        MCPManager instance
    """
    return _mcp_manager


def initialize_mcp_servers(mcp_config: Dict[str, Dict]) -> int:
    """Initialize all MCP servers from configuration.
    
    Args:
        mcp_config: Dict mapping server_name -> {transport, command/url, args/headers, etc}
                   Example: {
                       "filesystem": {
                           "transport": "stdio",
                           "command": "npx",
                           "args": ["@modelcontextprotocol/server-filesystem", "/path"]
                       },
                       "my-remote": {
                           "transport": "http",
                           "url": "https://mcp.example.com"
                       }
                   }
    
    Returns:
        Number of successfully connected servers
    """
    manager = get_mcp_manager()
    connected = 0
    
    for server_name, server_config in (mcp_config or {}).items():
        try:
            transport = server_config.get("transport", "stdio")
            
            # Prepare transport-specific config
            if transport == "stdio":
                config = {
                    "command": server_config.get("command"),
                    "args": server_config.get("args", []),
                    "env": server_config.get("env", {})
                }
            elif transport == "http":
                config = {
                    "url": server_config.get("url"),
                    "headers": server_config.get("headers", {})
                }
            else:
                logger.error(f"MCP: Unknown transport '{transport}' for server '{server_name}'")
                continue
            
            if manager.add_server(server_name, transport, config):
                connected += 1
        except Exception as e:
            logger.error(f"MCP: Failed to initialize server '{server_name}': {e}")
    
    stats = manager.stats()
    logger.info(f"MCP: Initialized {stats['servers_connected']}/{stats['servers_configured']} servers, "
                f"{stats['total_tools']} tools available")
    
    return connected
