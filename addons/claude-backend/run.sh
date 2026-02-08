#!/usr/bin/with-contenv bashio

# Get configuration from /data/options.json
CLAUDE_API_KEY=$(jq -r '.claude_api_key // ""' /data/options.json 2>/dev/null || echo "")
API_PORT=$(jq -r '.api_port // 5000' /data/options.json 2>/dev/null || echo "5000")
DEBUG_MODE=$(jq -r '.debug_mode // false' /data/options.json 2>/dev/null || echo "false")

# Export variables for Python app
export CLAUDE_API_KEY
export API_PORT
export DEBUG_MODE
export SUPERVISOR_TOKEN

# Start Claude Backend API
cd /app
exec python api.py
