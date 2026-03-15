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

    # Models that don't reliably emit native tool_calls via Groq —
    # they will use the XML tool simulator instead.
    _SIMULATOR_MODELS = {
        "moonshotai/kimi-k2-instruct-0905",
    }

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
                # Compress tool results to reduce token count (Groq TPM: 12k/min).
                # Strip old_yaml / new_yaml from JSON results — they're the biggest
                # token consumers and are not needed for follow-up decisions.
                # The diff and status fields are kept so the model has full context.
                safe_messages.append(self._compress_tool_result(m))
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

    @staticmethod
    def _compress_tool_result(msg: Dict[str, Any]) -> Dict[str, Any]:
        """Strip large YAML fields from tool result messages to save Groq TPM tokens.

        preview_automation_change and update_automation return old_yaml / new_yaml
        which can each be 400-800 tokens.  The model does not need the full YAML
        for follow-up decisions (confirm / cancel / next step) — it only needs
        the diff, status, and a brief summary.

        Fields removed: old_yaml, new_yaml
        Fields kept:    status, message, automation_id, diff, script_id, …
        """
        import json as _json
        content = msg.get("content", "")
        if not isinstance(content, str) or not content.strip().startswith("{"):
            return msg  # not JSON — leave as-is
        try:
            data = _json.loads(content)
            # Remove the two biggest fields
            compressed = {k: v for k, v in data.items() if k not in ("old_yaml", "new_yaml")}
            # Hard-cap any remaining long string (e.g. very long diff)
            for k, v in compressed.items():
                if isinstance(v, str) and len(v) > 600:
                    compressed[k] = v[:600] + "\n...[truncated for context length]"
            new_content = _json.dumps(compressed, ensure_ascii=False)
            if new_content == content:
                return msg  # nothing changed
            return {**msg, "content": new_content}
        except Exception:
            # Fallback: raw truncation if content is very long
            if len(content) > 800:
                return {**msg, "content": content[:800] + "\n...[truncated]"}
            return msg

    def uses_tool_simulator(self) -> bool:
        """Return True if the active model uses the XML tool simulator.

        Some Groq-hosted models (e.g. Kimi K2) accept tool schemas in the
        request but respond with plain text instead of tool_call deltas.
        For those models we fall back to the XML simulator so that tool
        actions are still executed correctly.
        """
        return (self.model or self.DEFAULT_MODEL) in self._SIMULATOR_MODELS

    def _stream_with_simulator(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream using the XML tool simulator (for models without native tool calling)."""
        tool_schemas = self._get_intent_tools(intent_info)
        msgs = self._prepare_messages(messages, intent_info)

        if tool_schemas:
            from providers.tool_simulator import get_simulator_system_prompt, flatten_tool_messages
            sim_prompt = get_simulator_system_prompt(tool_schemas)
            if msgs and msgs[0].get("role") == "system":
                existing = msgs[0].get("content") or ""
                msgs[0] = {"role": "system", "content": existing + "\n\n" + sim_prompt}
            else:
                msgs = [{"role": "system", "content": sim_prompt}] + msgs
            msgs = flatten_tool_messages(msgs)

        yield from self._openai_compat_stream(
            self.BASE_URL,
            self.api_key,
            self._get_model(),
            msgs,
            tools=None,  # no native tools — simulator handles them
            include_usage=self.INCLUDE_USAGE,
            max_tokens=self.MAX_TOKENS,
        )

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream with optional tool-simulator fallback for incompatible models."""
        if self.uses_tool_simulator():
            yield from self._stream_with_simulator(messages, intent_info)
            return

        # Try native tool calling; if the model doesn't support it, auto-fallback to simulator.
        try:
            items = list(super()._do_stream(messages, intent_info))
        except Exception as e:
            err_low = str(e).lower()
            if "tool calling" in err_low and "not supported" in err_low:
                model = self._get_model()
                logger.warning(
                    f"Groq: model '{model}' does not support native tool calling — "
                    f"falling back to XML tool simulator"
                )
                # Remember for this session so future rounds skip the failed attempt
                self._SIMULATOR_MODELS.add(model)
                yield from self._stream_with_simulator(messages, intent_info)
                return
            raise

        yield from items

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

        # Token / payload too large (413, TPM exceeded, or max_tokens constraint)
        # MUST come before _is_rate_limit_error because Groq sends
        # "rate_limit_exceeded" for TPM overages too.
        if ("413" in error_msg
                or "payload too large" in error_msg
                or "request too large" in error_msg
                or "tokens_limit_reached" in error_msg):
            return "Groq: token_limit (request too large)"
        if "max_tokens" in error_msg and "must be less than" in error_msg:
            return "Groq: token_limit (max_tokens exceeds model limit)"
        if self._is_auth_error(error_msg):
            return "Groq: API key invalid or missing. Check your Groq API key in the add-on settings."
        if self._is_rate_limit_error(error_msg):
            return "Groq: Rate limit exceeded. Please retry in a moment."
        if "tool calling" in error_msg and "not supported" in error_msg:
            return f"Groq: tool calling not supported by this model — switching to XML simulator"
        if "model_decommissioned" in error_msg or "decommissioned" in error_msg:
            return "Groq: This model has been decommissioned. Please select a different Groq model in the add-on settings."
        if "model" in error_msg and ("not found" in error_msg or "not available" in error_msg or "does not exist" in error_msg):
            return "Groq: Model not found or not available."

        return f"Groq error: {error}"
