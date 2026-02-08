#!/usr/bin/with-contenv bash
set -e

# source bashio functions if available
if [ -f /usr/lib/bashio/bashio.sh ]; then
    source /usr/lib/bashio/bashio.sh
else
    # Define simple log functions if bashio not available
    bashio::log.info() { echo "[INFO] $*"; }
    bashio::log.error() { echo "[ERROR] $*"; }
    bashio::log.warning() { echo "[WARNING] $*"; }
    bashio::log.debug() { echo "[DEBUG] $*"; }
fi

# Get configuration from /data/options.json
if [ -f /data/options.json ]; then
    HA_URL=$(jq -r '.ha_url // "http://homeassistant:8123"' /data/options.json)
    HA_TOKEN=$(jq -r '.ha_token // ""' /data/options.json)
    API_PORT=$(jq -r '.api_port // 5000' /data/options.json)
    DEBUG_MODE=$(jq -r '.debug_mode // false' /data/options.json)
    TIMEOUT=$(jq -r '.timeout // 30' /data/options.json)
    MAX_RETRIES=$(jq -r '.max_retries // 3' /data/options.json)
else
    # Use environment variables or defaults
    HA_URL="${HA_URL:-http://homeassistant:8123}"
    HA_TOKEN="${HA_TOKEN:-}"
    API_PORT="${API_PORT:-5000}"
    DEBUG_MODE="${DEBUG_MODE:-false}"
    TIMEOUT="${TIMEOUT:-30}"
    MAX_RETRIES="${MAX_RETRIES:-3}"
fi

# Log startup
bashio::log.info "🚀 Starting Claude Backend API Add-on..."
bashio::log.info "HA URL: $HA_URL"
bashio::log.info "API Port: $API_PORT"
bashio::log.info "Debug: $DEBUG_MODE"

# Export configuration as environment variables
export HA_URL
export HA_TOKEN
export API_PORT
export DEBUG_MODE
export TIMEOUT
export MAX_RETRIES

# Check if token exists
if [ -z "$HA_TOKEN" ]; then
    bashio::log.error "❌ HA_TOKEN not configured!"
    bashio::log.info "Please configure the Add-on with your Home Assistant token."
    bashio::log.info "Get a token from: Settings → Developer Tools → Long-lived access tokens"
    sleep 30
    exit 1
fi

bashio::log.info "✅ Token configured"

# ========================================
# STEP 1: Deploy Custom Component
# ========================================
bashio::log.info "📦 Deploying Claude custom component..."

COMPONENT_SRC="/app/claude_component"
COMPONENT_DST="/homeassistant/custom_components/claude"

if [ -d "$COMPONENT_SRC" ]; then
    # Create directory if it doesn't exist
    mkdir -p /homeassistant/custom_components
    
    # Remove old component if it exists
    if [ -d "$COMPONENT_DST" ]; then
        bashio::log.info "🔄 Removing old component version..."
        rm -rf "$COMPONENT_DST"
    fi
    
    # Copy new component
    cp -r "$COMPONENT_SRC" "$COMPONENT_DST"
    bashio::log.info "✅ Component deployed to $COMPONENT_DST"
else
    bashio::log.warning "⚠️ Component source not found at $COMPONENT_SRC"
fi

# ========================================
# STEP 2: Wait for Home Assistant to be ready
# ========================================
bashio::log.info "⏳ Waiting for Home Assistant to be ready..."

MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/" > /dev/null 2>&1; then
        bashio::log.info "✅ Home Assistant is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    bashio::log.debug "Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    bashio::log.error "❌ Home Assistant did not respond after $MAX_ATTEMPTS attempts"
    bashio::log.error "Check that HA_URL and HA_TOKEN are correct"
    sleep 30
    exit 1
fi

# ========================================
# STEP 3: Reload Home Assistant Core Config
# ========================================
bashio::log.info "🔄 Reloading Home Assistant to load Claude component..."

curl -s -X POST \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    "$HA_URL/api/config/core/reload" > /dev/null 2>&1 || bashio::log.warning "⚠️ Core reload request sent (may continue in background)"

# Wait for component to load
sleep 3

# ========================================
# STEP 4: Start Claude Backend API
# ========================================
bashio::log.info "🎯 Starting API server on port $API_PORT..."
bashio::log.info "================================================"
bashio::log.info "✅ Claude AI Backend is ready!"
bashio::log.info "================================================"
bashio::log.info "Next steps:"
bashio::log.info "1. Go to Settings → Devices & Services → Integrations"
bashio::log.info "2. Click 'Create Integration'"
bashio::log.info "3. Search for 'Claude'"
bashio::log.info "4. API Endpoint: http://localhost:5000"
bashio::log.info "5. Select your preferred model"
bashio::log.info "================================================"

cd /app
exec python api.py
