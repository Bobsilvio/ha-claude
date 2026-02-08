"""Flask API for Claude integration."""

import os
import logging
from typing import Any, Dict, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")
API_PORT = int(os.getenv("API_PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO)
logger = logging.getLogger(__name__)

# Home Assistant headers
HA_HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}


def call_ha_api(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call Home Assistant API."""
    url = f"{HA_URL}/api/{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HA_HEADERS, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HA_HEADERS, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=HA_HEADERS, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}

        if response.status_code in [200, 201]:
            return response.json() if response.text else {"status": "success"}
        else:
            logger.error(f"HA API error {response.status_code}: {response.text}")
            return {"error": f"API error {response.status_code}", "details": response.text}

    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"error": str(e)}


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "version": "1.0.0"}), 200


@app.route("/entities", methods=["GET"])
def get_entities():
    """Get all entities."""
    result = call_ha_api("GET", "states")
    
    if isinstance(result, list):
        return jsonify({
            "entities": {state["entity_id"]: state for state in result},
            "count": len(result)
        }), 200
    
    return jsonify(result), 500


@app.route("/automations", methods=["GET"])
def get_automations():
    """Get all automations."""
    result = call_ha_api("GET", "automations")
    
    if isinstance(result, list):
        return jsonify({
            "automations": {auto["id"]: auto for auto in result},
            "count": len(result)
        }), 200
    
    return jsonify(result), 500


@app.route("/scripts", methods=["GET"])
def get_scripts():
    """Get all scripts."""
    result = call_ha_api("GET", "scripts")
    
    if isinstance(result, list):
        return jsonify({
            "scripts": {script["id"]: script for script in result},
            "count": len(result)
        }), 200
    
    return jsonify(result), 500


@app.route("/entity/<entity_id>/state", methods=["GET"])
def get_entity_state(entity_id: str):
    """Get entity state."""
    result = call_ha_api("GET", f"states/{entity_id}")
    return jsonify(result), 200


@app.route("/message", methods=["POST"])
def send_message():
    """Send a message to Claude (placeholder for actual Claude integration)."""
    data = request.get_json()
    message = data.get("message", "")
    context = data.get("context", "")
    
    logger.info(f"Message received: {message}")
    
    # This would integrate with Claude API
    # For now, return success
    return jsonify({
        "status": "success",
        "message": message,
        "response": f"Processed: {message}"
    }), 200


@app.route("/execute/automation", methods=["POST"])
def execute_automation():
    """Execute an automation."""
    data = request.get_json()
    automation_id = data.get("automation_id", "")
    
    result = call_ha_api("POST", f"automations/{automation_id}/trigger", {})
    return jsonify(result), 200


@app.route("/execute/script", methods=["POST"])
def execute_script():
    """Execute a script."""
    data = request.get_json()
    script_id = data.get("script_id", "")
    variables = data.get("variables", {})
    
    result = call_ha_api("POST", f"services/script/{script_id}", variables)
    return jsonify(result), 200


@app.route("/service/call", methods=["POST"])
def call_service():
    """Call a Home Assistant service."""
    data = request.get_json()
    service = data.get("service", "")
    service_data = data.get("data", {})
    
    if not service or "." not in service:
        return jsonify({"error": "Invalid service format"}), 400
    
    domain, service_name = service.split(".", 1)
    result = call_ha_api("POST", f"services/{domain}/{service_name}", service_data)
    
    return jsonify(result), 200


@app.route("/webhook/<webhook_id>", methods=["POST"])
def webhook(webhook_id: str):
    """Handle webhooks from Claude."""
    data = request.get_json()
    logger.info(f"Webhook received: {webhook_id}")
    
    # Process webhook data
    # This is for bi-directional communication
    
    return jsonify({"status": "received"}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(f"Starting Claude API on port {API_PORT}")
    app.run(host="0.0.0.0", port=API_PORT, debug=DEBUG_MODE)
