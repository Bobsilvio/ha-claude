"""Constants for Claude integration."""

DOMAIN = "claude"
VERSION = "1.0.0"
MANUFACTURER = "Anthropic"

# Configuration keys
CONF_API_ENDPOINT = "api_endpoint"
CONF_MODEL = "model"
CONF_POLLING_INTERVAL = "polling_interval"
CONF_ENABLE_LOGGING = "enable_logging"
CONF_MAX_RETRIES = "max_retries"
CONF_TIMEOUT = "timeout"

# Available models
MODELS = ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]
DEFAULT_MODEL = "claude-3-haiku"

# Default values
DEFAULT_POLLING_INTERVAL = 60
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_API_ENDPOINT = "http://localhost:5000"

# Platforms
PLATFORMS = ["sensor", "switch", "light", "button"]

# Service names
SERVICE_SEND_MESSAGE = "send_message"
SERVICE_EXECUTE_AUTOMATION = "execute_automation"
SERVICE_EXECUTE_SCRIPT = "execute_script"
SERVICE_GET_ENTITY_STATE = "get_entity_state"
SERVICE_CALL_SERVICE = "call_service"
SERVICE_CREATE_AUTOMATION = "create_automation"

# Attributes
ATTR_MESSAGE = "message"
ATTR_CONTEXT = "context"
ATTR_RESPONSE = "response"
ATTR_AUTOMATION_ID = "automation_id"
ATTR_SCRIPT_ID = "script_id"
ATTR_VARIABLES = "variables"
ATTR_ENTITY_ID = "entity_id"
ATTR_SERVICE = "service"
ATTR_DATA = "data"
ATTR_AUTOMATION_NAME = "automation_name"
ATTR_TRIGGER = "trigger"
ATTR_CONDITION = "condition"
ATTR_ACTION = "action"
ATTR_DESCRIPTION = "description"
ATTR_STATUS = "status"

# States
STATE_CONNECTED = "connected"
STATE_DISCONNECTED = "disconnected"
STATE_ERROR = "error"
STATE_PROCESSING = "processing"

# Events
EVENT_MESSAGE_RECEIVED = f"{DOMAIN}_message_received"
EVENT_COMMAND_EXECUTED = f"{DOMAIN}_command_executed"
EVENT_ERROR = f"{DOMAIN}_error"

# Logger
LOGGER_NAME = f"{DOMAIN}"

# Model display names
MODEL_NAMES = {
    "claude-3-haiku": "Claude 3 Haiku",
    "claude-3-sonnet": "Claude 3 Sonnet",
    "claude-3-opus": "Claude 3 Opus",
}
