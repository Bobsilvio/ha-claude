#!/usr/bin/with-contenv bashio
set -e

bashio::log.info "══════════════════════════════════════════"
bashio::log.info " Claude AI Assistant v2.0"
bashio::log.info "══════════════════════════════════════════"

# Check API key
API_KEY=$(bashio::config 'anthropic_api_key')
if [ -z "$API_KEY" ]; then
    bashio::log.warning "Anthropic API key non configurata!"
    bashio::log.warning "Vai in Impostazioni → Add-ons → Claude AI → Configurazione"
fi

MODEL=$(bashio::config 'claude_model')
LANG=$(bashio::config 'language')

bashio::log.info "Modello: ${MODEL}"
bashio::log.info "Lingua: ${LANG}"
bashio::log.info "Ingress port: ${INGRESS_PORT:-8099}"
bashio::log.info "Supervisor token: disponibile"

# Start Flask application
bashio::log.info "Avvio server web..."
cd /app
exec python3 api.py
