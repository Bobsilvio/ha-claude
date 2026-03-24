"""WSGI entrypoint for the add-on.

Runs the Flask app using Waitress by importing `api` as a module.
This avoids duplicate module instances (__main__ vs api) that can desync globals
like AI_PROVIDER/AI_MODEL between the main app and provider modules.

If the main application fails to load (e.g. missing dependencies on ARM),
a lightweight diagnostic Flask app is started instead so that:
  1. The ingress port stays open (no "Cannot connect" errors).
  2. The user sees a clear error message in the browser.
  3. Logs contain the exact traceback for troubleshooting.
"""

from __future__ import annotations

import logging
import os
import platform
import signal
import sys
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("server")


# ── Optional-package audit (runs before heavy imports) ────────────────────────
def _check_optional_packages() -> dict[str, bool]:
    """Quick import-check for every optional dependency."""
    pkgs = [
        "anthropic", "openai", "google.genai", "httpx",
        "mcp", "telegram", "twilio", "discord",
        "PyPDF2", "docx",
    ]
    status: dict[str, bool] = {}
    for name in pkgs:
        try:
            __import__(name)
            status[name] = True
        except ImportError:
            status[name] = False
    return status


def _log_package_status(status: dict[str, bool]) -> None:
    missing = [k for k, v in status.items() if not v]
    available = [k for k, v in status.items() if v]
    if available:
        logger.info(f"Optional packages OK: {', '.join(available)}")
    if missing:
        logger.warning(f"Optional packages MISSING (features disabled): {', '.join(missing)}")


# ── Diagnostic fallback server ────────────────────────────────────────────────
def _run_diagnostic_server(error_msg: str, tb: str) -> None:
    """Start a minimal Flask app that shows the startup error."""
    try:
        from flask import Flask, jsonify
        from waitress import serve as waitress_serve

        port = int(os.environ.get("API_PORT", 5010))
        diag = Flask(__name__)

        arch = platform.machine()
        py_ver = platform.python_version()
        html_error = (
            f"<html><head><title>Amira – Startup Error</title>"
            f"<style>body{{font-family:monospace;padding:2em;background:#1a1a2e;color:#e0e0e0}}"
            f"h1{{color:#e74c3c}}pre{{background:#16213e;padding:1em;border-radius:8px;"
            f"overflow-x:auto;font-size:0.85em;color:#a8dadc}}"
            f".info{{color:#76c7c0}}</style></head>"
            f"<body><h1>⚠ Amira – Startup Failed</h1>"
            f"<p class='info'>Arch: {arch} | Python: {py_ver}</p>"
            f"<p>{error_msg}</p><pre>{tb}</pre>"
            f"<p>Check the add-on logs for details.</p></body></html>"
        )

        @diag.route("/", defaults={"path": ""})
        @diag.route("/<path:path>")
        def _catch_all(path):  # noqa: ARG001
            from flask import request as req
            if "html" in req.headers.get("Accept", ""):
                return html_error, 500
            return jsonify({
                "error": "startup_failed",
                "message": error_msg,
                "arch": arch,
                "python": py_ver,
            }), 500

        logger.info(f"Starting DIAGNOSTIC server on 0.0.0.0:{port} (main app failed)")
        waitress_serve(diag, host="0.0.0.0", port=port, threads=1)
    except Exception:
        logger.critical("Diagnostic server also failed — exiting.")
        logger.critical(traceback.format_exc())
        sys.exit(1)


# ── Main entry ────────────────────────────────────────────────────────────────
def main() -> None:
    logger.info(f"Platform: {platform.machine()} | Python {platform.python_version()} | PID {os.getpid()}")

    # Audit optional packages first
    pkg_status = _check_optional_packages()
    _log_package_status(pkg_status)

    # Try loading the main application
    try:
        import api  # noqa: E402  — heavy import, may fail on ARM
    except Exception as exc:
        logger.critical(f"FATAL: Failed to import api module: {exc}")
        logger.critical(traceback.format_exc())
        _run_diagnostic_server(str(exc), traceback.format_exc())
        return

    # Normal startup
    api.logger.info(f"Provider: {api.AI_PROVIDER} | Model: {api.get_active_model()}")
    api.logger.info(f"API Key: {'configured' if api.get_api_key() else 'NOT configured'}")
    api.logger.info(f"HA Token: {'available' if api.get_ha_token() else 'NOT available'}")
    api.logger.info(f"Log Level: {api.LOG_LEVEL.upper()} | Colored Logs: {api.COLORED_LOGS} | Debug Mode: {api.DEBUG_MODE}")
    api.logger.info(
        f"Features: Memory={api.ENABLE_MEMORY} | "
        f"FileUpload={api.ENABLE_FILE_UPLOAD} | RAG={api.ENABLE_RAG} | "
        f"ChatBubble={api.ENABLE_CHAT_BUBBLE}"
    )

    # Validate provider/model compatibility
    is_valid, error_msg = api.validate_model_provider_compatibility()
    if not is_valid:
        api.logger.warning(error_msg)
        # Auto-fix: reset to provider default model
        default_model = api.PROVIDER_DEFAULTS.get(api.AI_PROVIDER, {}).get("model", "")
        if default_model:
            api.AI_MODEL = default_model
            fix_msgs = {
                "en": f"✅ AUTO-FIX: Model automatically changed to '{api.MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (default for {api.AI_PROVIDER})",
                "it": f"✅ AUTO-FIX: Modello cambiato automaticamente a '{api.MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (default per {api.AI_PROVIDER})",
                "es": f"✅ AUTO-FIX: Modelo cambiado automáticamente a '{api.MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (predeterminado para {api.AI_PROVIDER})",
                "fr": f"✅ AUTO-FIX: Modèle changé automatiquement en '{api.MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (par défaut pour {api.AI_PROVIDER})",
            }
            api.logger.warning(fix_msgs.get(api.LANGUAGE, fix_msgs["en"]))

    # Register floating chat bubble (if enabled)
    api.setup_chat_bubble()

    # Cleanup bubble resources on graceful shutdown (SIGTERM sent by HA on stop/delete)
    def _sigterm_handler(signum, frame):
        api.logger.info("SIGTERM received — cleaning up Amira Lovelace resources before exit")
        try:
            api.cleanup_chat_bubble()
            api.logger.info("Chat bubble cleanup complete")
        except Exception as e:
            api.logger.warning(f"Cleanup on shutdown failed: {e}")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _sigterm_handler)

    # Start Telegram / WhatsApp / Discord bots if configured
    api.start_messaging_bots()

    # Initialize MCP servers if configured
    api.initialize_mcp()

    from waitress import serve

    api.logger.info(f"Starting production server on 0.0.0.0:{api.API_PORT}")
    serve(api.app, host="0.0.0.0", port=api.API_PORT, threads=6)


if __name__ == "__main__":
    main()
