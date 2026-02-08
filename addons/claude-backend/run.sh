#!/usr/bin/with-contenv bashio
set -e

# Get configuration
HA_URL=$(bashio::config 'ha_url')
HA_TOKEN=$(bashio::config 'ha_token')
API_PORT=$(bashio::config 'api_port')
DEBUG_MODE=$(bashio::config 'debug_mode')
TIMEOUT=$(bashio::config 'timeout')
MAX_RETRIES=$(bashio::config 'max_retries')

# Log startup
bashio::log.info "Starting Claude Backend API..."
bashio::log.info "Home Assistant URL: $HA_URL"
bashio::log.info "API Port: $API_PORT"
bashio::log.info "Debug Mode: $DEBUG_MODE"

# Export configuration as environment variables
export HA_URL="$HA_URL"
export HA_TOKEN="${HA_TOKEN:-$(bashio::config 'ha_token' '')}"
export API_PORT="$API_PORT"
export DEBUG_MODE="$DEBUG_MODE"
export TIMEOUT="$TIMEOUT"
export MAX_RETRIES="$MAX_RETRIES"

# Get Token from Home Assistant
if [ -z "$HA_TOKEN" ]; then
    bashio::log.warning "HA_TOKEN not configured. Please add your token in add-on options."
    bashio::log.info "Get a long-lived token from Settings → Developer Tools → Long-lived access tokens"
fi

# Start API
bashio::log.info "Starting API server on port $API_PORT..."
cd /app
python api.py
