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
        try:
            import api as _api  # type: ignore
            _base_timeout = int(getattr(_api, "TIMEOUT", 30) or 30)
        except Exception:
            _base_timeout = 30
        _base_timeout = max(30, min(300, _base_timeout))
        model = (self.model or "gemini-2.0-flash").replace("google/", "")
        # Guard: models that only support the Interactions API cannot use
        # the standard streamGenerateContent endpoint.
        if model.startswith("deep-research"):
            raise RuntimeError(
                f"Il modello '{model}' supporta solo la Interactions API di Google "
                f"e non è compatibile con la chat. "
                f"Seleziona un modello Gemini standard (es. gemini-2.0-flash)."
            )
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
        _is_html_intent = bool(
            isinstance(intent_info, dict)
            and str(intent_info.get("intent", "")).lower() == "create_html_dashboard"
        )
        # HTML dashboards are often long and risk getting cut mid-output.
        # Allow larger output budget for this intent.
        _max_output_tokens = 16384 if _is_html_intent else 8192
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": _max_output_tokens},
        }
        def _sanitize_tool_schema(obj: Any) -> Any:
            if isinstance(obj, dict):
                out: Dict[str, Any] = {}
                for k, v in obj.items():
                    if k == "enum" and isinstance(v, list):
                        vals = []
                        for item in v:
                            if item is None:
                                continue
                            if isinstance(item, str) and item.strip() == "":
                                continue
                            vals.append(_sanitize_tool_schema(item))
                        if vals:
                            out[k] = vals
                        continue
                    if k == "required" and isinstance(v, list):
                        req = [item for item in v if isinstance(item, str) and item.strip()]
                        if req:
                            out[k] = req
                        continue
                    out[k] = _sanitize_tool_schema(v)
                return out
            if isinstance(obj, list):
                return [_sanitize_tool_schema(x) for x in obj]
            return obj
        # Enable native Gemini function calling using the existing OpenAI-format
        # tool schemas injected by api.py (intent_info["tool_schemas"]).
        _tool_schemas = self._get_intent_tools(intent_info) or []
        if _tool_schemas:
            _decls: List[Dict[str, Any]] = []
            for _t in _tool_schemas:
                _fn = (_t or {}).get("function") if isinstance(_t, dict) else None
                if not isinstance(_fn, dict):
                    continue
                _name = str(_fn.get("name") or "").strip()
                if not _name:
                    continue
                _decl = {
                    "name": _name,
                    "description": str(_fn.get("description") or ""),
                    "parameters": _sanitize_tool_schema(
                        _fn.get("parameters") or {"type": "object", "properties": {}}
                    ),
                }
                _decls.append(_decl)
            if _decls:
                body["tools"] = [{"functionDeclarations": _decls}]
                # Keep AUTO for stability: forcing ANY on large HTML payloads can
                # trigger malformed_function_call with some Gemini versions.
                _fc_cfg: Dict[str, Any] = {"mode": "AUTO"}
                body["toolConfig"] = {"functionCallingConfig": _fc_cfg}
                logger.info("google: function-calling enabled (%s declarations)", len(_decls))
        if system.strip():
            body["systemInstruction"] = {"parts": [{"text": system.strip()}]}
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:streamGenerateContent?key={self.api_key}&alt=sse"
        )
        _timeout = httpx.Timeout(
            connect=float(min(20, _base_timeout)),
            read=float(max(180, _base_timeout * 6)),
            write=float(min(30, max(15, _base_timeout // 2))),
            pool=10.0,
        )
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
            captured_usage = None
            final_finish_reason = "stop"
            saw_text = False
            text_chunks: List[str] = []
            # Gemini may emit functionCall parts instead of (or alongside) text.
            accumulated_tool_calls: List[Dict[str, Any]] = []
            seen_tool_sigs = set()
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str:
                    continue
                try:
                    event = json.loads(data_str)
                    # Google returns usageMetadata in SSE chunks
                    um = event.get("usageMetadata")
                    if um:
                        captured_usage = {
                            "input_tokens": um.get("promptTokenCount", 0) or 0,
                            "output_tokens": um.get("candidatesTokenCount", 0) or 0,
                            "cache_read_tokens": um.get("cachedContentTokenCount", 0) or 0,
                        }
                    candidates = event.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                saw_text = True
                                text_chunks.append(text)
                                yield {"type": "text", "text": text}
                            fc = part.get("functionCall") if isinstance(part, dict) else None
                            if isinstance(fc, dict) and fc.get("name"):
                                _name = str(fc.get("name", "")).strip()
                                _args_obj = fc.get("args")
                                if isinstance(_args_obj, str):
                                    _args_json = _args_obj
                                else:
                                    _args_json = json.dumps(_args_obj or {}, ensure_ascii=False)
                                _sig = f"{_name}:{_args_json}"
                                if _sig not in seen_tool_sigs:
                                    seen_tool_sigs.add(_sig)
                                    accumulated_tool_calls.append({
                                        "id": f"call_{_name}_{len(accumulated_tool_calls)}",
                                        "name": _name,
                                        "arguments": _args_json,
                                    })
                        finish = candidates[0].get("finishReason", "")
                        if finish and finish not in ("", "STOP_REASON_UNSPECIFIED"):
                            final_finish_reason = str(finish).lower()
                except json.JSONDecodeError:
                    continue
        try:
            logger.info(
                "google: stream finished with reason=%s (prompt=%s, candidates=%s, maxOutputTokens=%s, tool_calls=%s)",
                final_finish_reason,
                (captured_usage or {}).get("input_tokens", 0),
                (captured_usage or {}).get("output_tokens", 0),
                _max_output_tokens,
                len(accumulated_tool_calls),
            )
        except Exception:
            pass
        done_evt_final: dict = {"type": "done", "finish_reason": final_finish_reason or "stop"}
        if captured_usage:
            done_evt_final["usage"] = captured_usage
        if accumulated_tool_calls:
            done_evt_final["tool_calls"] = self._normalize_tool_calls(
                accumulated_tool_calls, tools=_tool_schemas
            )
        if (
            not done_evt_final.get("tool_calls")
            and _tool_schemas
            and str(final_finish_reason or "").lower() in {"malformed_function_call", "function_call"}
            and text_chunks
        ):
            recovered = self._recover_tool_calls_from_text(
                "".join(text_chunks), tools=_tool_schemas
            )
            if recovered:
                logger.info("google: recovered %s tool_call(s) from malformed response text", len(recovered))
                done_evt_final["tool_calls"] = recovered
                done_evt_final["finish_reason"] = "tool_calls"
        if (
            final_finish_reason == "malformed_function_call"
            and not accumulated_tool_calls
            and not saw_text
        ):
            # Avoid silent failure in chat UI when Gemini emits no text and no
            # executable tool call.
            logger.warning(
                "google: malformed_function_call with empty payload "
                "(no text, no tool_calls). Returning explicit error event."
            )
            yield {
                "type": "error",
                "message": (
                    "Google/Gemini returned malformed_function_call (nessun tool valido). "
                    "Riprova oppure riduci il prompt."
                ),
            }
            return
        yield done_evt_final

    def get_available_models(self) -> List[str]:
        return [
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
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
