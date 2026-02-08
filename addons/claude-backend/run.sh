#!/usr/bin/with-contenv bashio

# Get configuration using bashio (Home Assistant way)
CLAUDE_API_KEY=$(bashio::config 'claude_api_key')
API_PORT=$(bashio::config 'api_port' 5000)
DEBUG_MODE=$(bashio::config 'debug_mode' false)

# Export variables for Python app
export CLAUDE_API_KEY
export API_PORT
export DEBUG_MODE
export SUPERVISOR_TOKEN

# Start Claude Backend API
cd /app
exec python api.py
