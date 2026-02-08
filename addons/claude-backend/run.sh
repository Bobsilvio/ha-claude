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
bashio::log.info "Starting Claude Backend API Add-on..."
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
    bashio::log.error "HA_TOKEN not configured!"
    bashio::log.info "Please add your token in add-on options."
    bashio::log.info "Get a long-lived token from Settings → Developer Tools → Long-lived access tokens"
    exit 1
fi

# ========================================
# STEP 1: Deploy Custom Component
# ========================================
bashio::log.info "Deploying Claude custom component..."

COMPONENT_SRC="/app/claude_component"
COMPONENT_DST="/homeassistant/custom_components/claude"

if [ -d "$COMPONENT_SRC" ]; then
    # Create directory if it doesn't exist
    mkdir -p /homeassistant/custom_components
    
    # Remove old component if it exists
    if [ -d "$COMPONENT_DST" ]; then
        bashio::log.info "Removing old component version..."
        rm -rf "$COMPONENT_DST"
    fi
    
    # Copy new component
    cp -r "$COMPONENT_SRC" "$COMPONENT_DST"
    bashio::log.info "✓ Component deployed to $COMPONENT_DST"
else
    bashio::log.warning "Component source not found at $COMPONENT_SRC"
fi

# ========================================
# STEP 2: Wait for Home Assistant to be ready
# ========================================
bashio::log.info "Waiting for Home Assistant to be ready..."

MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/" > /dev/null 2>&1; then
        bashio::log.info "✓ Home Assistant is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    bashio::log.debug "Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    bashio::log.error "Home Assistant did not respond after $MAX_ATTEMPTS attempts"
    bashio::log.error "Check that HA_URL and HA_TOKEN are correct"
    exit 1
fi

# ========================================
# STEP 3: Reload Home Assistant
# ========================================
bashio::log.info "Reloading Home Assistant to load Claude component..."

RELOAD_RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    "$HA_URL/api/config/core/reload" 2>&1)

if echo "$RELOAD_RESPONSE" | grep -q '"success": true\|"type": "core_config_updated"'; then
    bashio::log.info "✓ Home Assistant reloaded successfully"
else
    bashio::log.warning "Home Assistant reload response: $RELOAD_RESPONSE"
fi

# Wait a bit for component to load
sleep 3

# ========================================
# STEP 4: Start Claude Backend API
# ========================================
bashio::log.info "Starting API server on port $API_PORT..."
bashio::log.info "================================================"
bashio::log.info "Claude AI Backend is ready!"
bashio::log.info "================================================"
bashio::log.info "Next steps:"
bashio::log.info "1. Go to Settings → Devices & Services → Integrations"
bashio::log.info "2. Click 'Create Integration'"
bashio::log.info "3. Search for 'Claude'"
bashio::log.info "4. API Endpoint: http://localhost:5000"
bashio::log.info "5. Select your preferred model"
bashio::log.info "================================================"

cd /app
python api.py
