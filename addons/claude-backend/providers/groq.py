"""Groq provider - Fast inference for open-source models via Groq API.

Groq specializes in fast inference for open-source models like Mixtral, LLaMA, etc.
Uses the OpenAI-compatible API format but with Groq's endpoints.
"""

import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class GroqProvider(EnhancedProvider):
    """Provider adapter for Groq API (OpenAI-compatible).

    Inherits the standard _do_stream() from EnhancedProvider.
    Overrides _prepare_messages() to sanitize Anthropic-format list content
    and to preserve tool messages during agentic tool-calling rounds.
    """

    # --- Provider contract ---
    BASE_URL      = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    INCLUDE_USAGE = True
    # -------------------------

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize Groq provider."""
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "groq"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate Groq API key is configured."""
        if not self.api_key:
            return False, "Groq API key not configured"
        return True, ""

    def _prepare_messages(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Prepare and sanitize messages for Groq API.

        Groq requires:
        - Only 'user', 'assistant', 'system', and 'tool' (when tool calling) roles
        - String content (not list-of-blocks Anthropic format)
        - Preservation of tool/assistant-with-tool_calls messages during tool rounds
        """
        # Inject intent system prompt via base class
        messages = super()._prepare_messages(messages, intent_info)

        tool_schemas = self._get_intent_tools(intent_info)
        has_tools = bool(tool_schemas)

        safe_messages = []
        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "")
            # Pass through tool role and assistant-with-tool_calls when tools are active
            if has_tools and role == "tool":
                safe_messages.append(m)
                continue
            if has_tools and role == "assistant" and m.get("tool_calls"):
                safe_messages.append(m)
                continue
            if role not in ("user", "assistant", "system"):
                continue  # skip unsupported roles
            if isinstance(content, list):
                # Flatten list of content blocks to plain text
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text") or block.get("content") or ""
                        if text:
                            parts.append(str(text))
                    elif isinstance(block, str):
                        parts.append(block)
                content = "\n".join(parts) if parts else ""
            if not isinstance(content, str):
                content = str(content)
            if content or role == "system":
                safe_messages.append({"role": role, "content": content})
        return safe_messages

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat completion using Groq API.

        Groq provides OpenAI-compatible streaming with very fast inference.
        """
        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.name)

        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")

        self.rate_limiter.record_request()

        # Use enhanced caching and retry
        yield from self.stream_chat_with_caching(messages, intent_info, max_retries=3)

    def get_available_models(self) -> List[str]:
        return [
            # Production models
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            # Production systems (agentic)
            "groq/compound",
            "groq/compound-mini",
            # Preview models
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "qwen/qwen3-32b",
            "moonshotai/kimi-k2-instruct-0905",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get Groq-specific error translations."""
        return {
            "auth_error": {
                "en": "Groq: API key invalid or missing. Check your Groq API key in the add-on settings.",
                "it": "Groq: Chiave API non valida o mancante. Controlla la chiave API Groq nelle impostazioni del componente aggiuntivo.",
                "es": "Groq: Clave API inválida o faltante. Comprueba tu clave API de Groq en la configuración del complemento.",
                "fr": "Groq: Clé API invalide ou manquante. Vérifiez votre clé API Groq dans les paramètres du module complémentaire.",
            },
            "rate_limit": {
                "en": "Groq: Rate limit exceeded. Please retry in a moment.",
                "it": "Groq: Limite di velocità superato. Riprova tra un momento.",
                "es": "Groq: Límite de velocidad excedido. Vuelva a intentarlo en un momento.",
                "fr": "Groq: Limite de débit dépassée. Veuillez réessayer dans un instant.",
            },
            "model_not_found": {
                "en": "Groq: Model not found or not available.",
                "it": "Groq: Modello non trovato o non disponibile.",
                "es": "Groq: Modelo no encontrado o no disponible.",
                "fr": "Groq: Modèle non trouvé ou non disponible.",
            },
            "connection_error": {
                "en": "Groq: Connection error. Check your internet connection.",
                "it": "Groq: Errore di connessione. Controlla la tua connessione Internet.",
                "es": "Groq: Error de conexión. Comprueba tu conexión a Internet.",
                "fr": "Groq: Erreur de connexion. Vérifiez votre connexion Internet.",
            },
            "timeout": {
                "en": "Groq: Request timeout. The model may be overloaded or the response is taking too long.",
                "it": "Groq: Timeout della richiesta. Il modello potrebbe essere sovraccarico o la risposta richiede troppo tempo.",
                "es": "Groq: Timeout de la solicitud. El modelo puede estar sobrecargado o la respuesta está tardando demasiado.",
                "fr": "Groq: Délai d'attente dépassé. Le modèle peut être surchargé ou la réponse prend trop de temps.",
            },
        }

    def normalize_error_message(self, error: Exception) -> str:
        """Convert Groq API error to user-friendly message."""
        error_msg = str(error).lower()

        if self._is_auth_error(error_msg):
            return "Groq: API key invalid or missing. Check your Groq API key in the add-on settings."
        if self._is_rate_limit_error(error_msg):
            return "Groq: Rate limit exceeded. Please retry in a moment."
        if "model_decommissioned" in error_msg or "decommissioned" in error_msg:
            return "Groq: This model has been decommissioned. Please select a different Groq model in the add-on settings."
        if "model" in error_msg:
            return "Groq: Model not found or not available."

        return f"Groq error: {error}"
