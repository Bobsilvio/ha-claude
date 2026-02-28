"""Google Gemini provider adapter with enhanced error handling and rate limiting.

Extends EnhancedProvider for automatic retry, caching, and intelligent fallback.
"""

import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class GoogleProvider(EnhancedProvider):
    """Enhanced provider adapter for Google Gemini models."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize Google provider with enhanced features."""
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "google"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate Google API key is configured."""
        if not self.api_key:
            return False, "Google API key not configured"
        return True, ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat with automatic retry, caching, and rate limiting.
        
        Features:
        - Automatic retry with exponential backoff
        - Integrated prompt caching
        - Per-provider rate limit tracking
        """
        # Initialize rate limiter on first use
        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.name)
        
        # Check rate limit before streaming
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        
        # Record request for rate limiting
        self.rate_limiter.record_request()
        
        # Stream with automatic retry and caching integration
        try:
            yield from self.stream_chat_with_caching(messages, intent_info, max_retries=2)
        except Exception as e:
            logger.error(f"{self.name}: Error during streaming: {e}")
            raise

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Actual Google Gemini API call via httpx REST."""
        import json
        import httpx
        model = (self.model or "gemini-2.0-flash").replace("google/", "")
        system = ""
        contents = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system += (content if isinstance(content, str) else "") + "\n"
            else:
                text = content if isinstance(content, str) else ""
                g_role = "model" if role == "assistant" else "user"
                if text:
                    contents.append({"role": g_role, "parts": [{"text": text}]})
        if not contents:
            return
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 8192},
        }
        if system.strip():
            body["systemInstruction"] = {"parts": [{"text": system.strip()}]}
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:streamGenerateContent?key={self.api_key}&alt=sse"
        )
        _timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=5.0)
        with httpx.stream("POST", url, json=body, timeout=_timeout) as response:
            if response.status_code != 200:
                error_text = response.read().decode("utf-8", errors="ignore")
                # Quota esaurita = errore permanente, non ha senso ritentare
                if response.status_code == 429 and (
                    "insufficient_quota" in error_text
                    or "exceeded your current quota" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                ):
                    raise RuntimeError(f"Google: quota esaurita. Controlla il piano e la fatturazione su ai.google.dev. (HTTP 429)")
                raise RuntimeError(f"Google HTTP {response.status_code}: {error_text[:300]}")
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str:
                    continue
                try:
                    event = json.loads(data_str)
                    candidates = event.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield {"type": "text", "text": text}
                        finish = candidates[0].get("finishReason", "")
                        if finish and finish not in ("", "STOP_REASON_UNSPECIFIED"):
                            yield {"type": "done", "finish_reason": finish.lower()}
                except json.JSONDecodeError:
                    continue
        yield {"type": "done", "finish_reason": "stop"}

    def get_available_models(self) -> List[str]:
        return [
            "gemini-2.0-flash",
            "gemini-2.0-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get Google-specific error translations."""
        return {
            "rate_limit": {
                "en": "Google: Rate limit exceeded. Please retry in a moment.",
                "it": "Google: Limite di velocità superato. Riprova tra poco.",
                "es": "Google: Límite de velocidad excedido. Intenta de nuevo en un momento.",
                "fr": "Google: Limite de vitesse dépassée. Réessayez dans un moment.",
            },
            "auth_error": {
                "en": "Google: API key invalid or missing. Check your Google API key in settings.",
                "it": "Google: Chiave API non valida o mancante. Controlla le impostazioni.",
                "es": "Google: Clave API inválida o faltante. Verifica la configuración.",
                "fr": "Google: Clé API invalide ou manquante. Vérifiez les paramètres.",
            },
            "quota_exceeded": {
                "en": "Google: API quota exceeded or billing not enabled. Check your Cloud project.",
                "it": "Google: Quota API superata o billing non abilitato. Controlla il progetto.",
                "es": "Google: Cuota de API superada o facturación no habilitada. Verifica el proyecto.",
                "fr": "Google: Quota API dépassé ou facturation non activée. Vérifiez le projet.",
            },
            "permission_denied": {
                "en": "Google: Permission denied. Check your API key and project permissions.",
                "it": "Google: Permesso negato. Controlla la chiave API e i permessi del progetto.",
                "es": "Google: Permiso denegado. Verifica la clave API y los permisos del proyecto.",
                "fr": "Google: Permission refusée. Vérifiez la clé API et les permissions du projet.",
            },
        }
