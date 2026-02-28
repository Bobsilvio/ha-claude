"""Ollama provider - Run LLMs locally using Ollama.

Ollama allows running open-source LLMs (LLaMA, Mistral, etc.) on local hardware.
Perfect for privacy-conscious deployments and for development.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class OllamaProvider(EnhancedProvider):
    """Provider adapter for Ollama (local LLM inference)."""

    def __init__(self, api_key: str = "", model: str = "", base_url: str = ""):
        """Initialize Ollama provider.
        
        Args:
            api_key: Not used for Ollama (local), keeping for interface compatibility
            model: Model name (e.g., 'llama2', 'mistral', 'neural-chat')
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        super().__init__(api_key, model)
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "ollama"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate Ollama is accessible on localhost.
        
        Ollama doesn't require API keys, but needs to be running locally.
        """
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                return True, ""
            return False, "Ollama server not responding correctly"
        except Exception as e:
            return False, f"Ollama not accessible at {self.base_url}: {e}"

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat completion using Ollama.
        
        Ollama provides a REST API with streaming support (Server-Sent Events).
        """
        # Rate limiting check
        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.name)
        
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        
        self.rate_limiter.record_request()
        
        # Use enhanced caching and retry
        yield from self.stream_chat_with_caching(messages, intent_info, max_retries=2)

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Actual Ollama local API call via httpx with tool calling support."""
        import json
        import httpx
        model = self.model or "llama2"
        base_url = getattr(self, "base_url", "http://localhost:11434")
        _timeout = httpx.Timeout(connect=10.0, read=180.0, write=10.0, pool=5.0)

        # Include tool schemas if provided by intent (models that support tool calling)
        tool_schemas = (intent_info or {}).get("tool_schemas") or []
        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if tool_schemas:
            body["tools"] = tool_schemas

        accumulated_tool_calls: Dict[int, Dict] = {}

        with httpx.stream(
            "POST", f"{base_url}/api/chat",
            json=body,
            timeout=_timeout,
        ) as response:
            if response.status_code != 200:
                error_text = response.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"Ollama HTTP {response.status_code}: {error_text[:300]}")
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    msg = event.get("message") or {}

                    # Text content
                    content = msg.get("content", "")
                    if content:
                        yield {"type": "text", "text": content}

                    # Tool calls (Ollama returns them in message.tool_calls)
                    for tc in msg.get("tool_calls") or []:
                        fn = tc.get("function") or {}
                        name = fn.get("name", "")
                        args = fn.get("arguments") or {}
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {}
                        if name:
                            idx = len(accumulated_tool_calls)
                            accumulated_tool_calls[idx] = {
                                "id": f"ollama_{idx}",
                                "type": "function",
                                "function": {"name": name, "arguments": json.dumps(args)},
                            }

                    if event.get("done"):
                        done_event: Dict[str, Any] = {"type": "done", "finish_reason": "stop"}
                        if accumulated_tool_calls:
                            done_event["finish_reason"] = "tool_calls"
                            done_event["tool_calls"] = list(accumulated_tool_calls.values())
                        yield done_event

                except json.JSONDecodeError:
                    continue

    def get_available_models(self) -> List[str]:
        """
        Fetches live list from Ollama API if available, otherwise returns defaults.
        """
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if "models" in data:
                    return [m.get("name", "") for m in data["models"]]
        except Exception:
            pass

        # Fallback: return common locally-available models
        return [
            "mistral",
            "llama2",
            "neural-chat",
            "orca-mini",
            "dolphin-mixtral",
            "openchat",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get Ollama-specific error translations."""
        return {
            "connection_error": {
                "en": f"Ollama: Not accessible at {self.base_url}. Make sure Ollama is running locally.",
                "it": f"Ollama: Non accessibile su {self.base_url}. Assicurati che Ollama sia in esecuzione localmente.",
                "es": f"Ollama: No accesible en {self.base_url}. Asegúrate de que Ollama se está ejecutando localmente.",
                "fr": f"Ollama: Non accessible sur {self.base_url}. Assurez-vous qu'Ollama s'exécute localement.",
            },
            "timeout": {
                "en": "Ollama: Request timeout. Ollama might be busy or non-responsive.",
                "it": "Ollama: Timeout della richiesta. Ollama potrebbe essere occupato o non reattivo.",
                "es": "Ollama: Timeout de la solicitud. Ollama podría estar ocupado o no responder.",
                "fr": "Ollama: Délai d'attente de la demande. Ollama peut être occupé ou ne pas répondre.",
            },
            "model_not_found": {
                "en": "Ollama: Model not found. Make sure it's installed with 'ollama pull <model>'.",
                "it": "Ollama: Modello non trovato. Assicurati che sia installato con 'ollama pull <model>'.",
                "es": "Ollama: Modelo no encontrado. Asegúrate de que esté instalado con 'ollama pull <model>'.",
                "fr": "Ollama: Modèle non trouvé. Assurez-vous qu'il est installé avec 'ollama pull <model>'.",
            },
            "server_error": {
                "en": "Ollama: Server error. Check the Ollama logs for details.",
                "it": "Ollama: Errore del server. Controlla i log di Ollama per i dettagli.",
                "es": "Ollama: Error del servidor. Comprueba los registros de Ollama para obtener detalles.",
                "fr": "Ollama: Erreur serveur. Vérifiez les journaux Ollama pour plus de détails.",
            },
        }

    def normalize_error_message(self, error: Exception) -> str:
        """Convert Ollama error to user-friendly message."""
        error_msg = str(error).lower()

        if "connection" in error_msg or "refused" in error_msg:
            return f"Ollama: Not accessible at {self.base_url}. Make sure Ollama is running locally."
        if "timeout" in error_msg:
            return "Ollama: Request timeout. Ollama might be busy or non-responsive."
        if "model" in error_msg:
            return "Ollama: Model not found. Make sure it's installed with 'ollama pull <model>'."

        return f"Ollama error: {error}"
