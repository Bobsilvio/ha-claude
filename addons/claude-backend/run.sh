#!/usr/bin/with-contenv bash
set -e

# Initialize logging
log_info() { echo "[INFO] $*"; }
log_error() { echo "[ERROR] $*"; }
log_warning() { echo "[WARNING] $*"; }

# Try to use bashio if available
if [ -f /usr/lib/bashio/bashio.sh ]; then
    source /usr/lib/bashio/bashio.sh
    log_info() { bashio::log.info "$*"; }
    log_error() { bashio::log.error "$*"; }
    log_warning() { bashio::log.warning "$*"; }
fi

# Get configuration from /data/options.json
if [ -f /data/options.json ] && command -v jq &> /dev/null; then
    HA_URL=$(jq -r '.ha_url // "http://homeassistant:8123"' /data/options.json 2>/dev/null || echo "http://homeassistant:8123")
    HA_TOKEN=$(jq -r '.ha_token // ""' /data/options.json 2>/dev/null || echo "")
    CLAUDE_API_KEY=$(jq -r '.claude_api_key // ""' /data/options.json 2>/dev/null || echo "")
    API_PORT=$(jq -r '.api_port // 5000' /data/options.json 2>/dev/null || echo "5000")
    DEBUG_MODE=$(jq -r '.debug_mode // false' /data/options.json 2>/dev/null || echo "false")
else
    # Use environment variables or defaults
    HA_URL="${HA_URL:-http://homeassistant:8123}"
    HA_TOKEN="${HA_TOKEN:-}"
    CLAUDE_API_KEY="${CLAUDE_API_KEY:-}"
    API_PORT="${API_PORT:-5000}"
    DEBUG_MODE="${DEBUG_MODE:-false}"
fi

log_info "🚀 Starting Claude Backend API Add-on (v2.0.1)"
log_info "HA URL: $HA_URL"
log_info "API Port: $API_PORT"

# Check if token exists
if [ -z "$HA_TOKEN" ]; then
    log_error "❌ HA_TOKEN not configured!"
    log_info "Please configure the Add-on with your Home Assistant token."
    log_info "Get a token from: Settings → Developer Tools → Long-lived access tokens"
    sleep 30
    exit 1
fi

if [ -z "$CLAUDE_API_KEY" ]; then
    log_error "❌ CLAUDE_API_KEY not configured!"
    log_info "Please configure the Add-on with your Anthropic Claude API key."
    log_info "Get a key from: https://console.anthropic.com/"
    sleep 30
    exit 1
fi

log_info "✅ Tokens configured"

# ========================================
# Start Claude Backend API
# ========================================
log_info "🎯 Starting API server on port $API_PORT..."
log_info "🤖 Claude AI will be available in the sidebar (Ingress)"
log_info "✅ Claude AI Backend is ready!"

export HA_URL
export HA_TOKEN
export CLAUDE_API_KEY
export API_PORT
export DEBUG_MODE

cd /app
exec python api.py
