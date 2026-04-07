"""Anthropic provider adapter with enhanced error handling and rate limiting.

Extends EnhancedProvider for automatic retry, caching, and MCP auth support.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)

# Anthropic requires tool IDs to match ^[a-zA-Z0-9_-]+$
_TOOL_ID_CLEAN_RE = re.compile(r'[^a-zA-Z0-9_-]')
_tool_id_seq = 0


def _sanitize_tool_id(raw_id: str, fallback_name: str = "unknown") -> str:
    """Sanitize a tool ID to match Anthropic's required pattern ^[a-zA-Z0-9_-]+$.

    Replaces invalid characters with underscores.  Generates a unique fallback
    when the ID is empty or entirely composed of invalid characters.
    """
    global _tool_id_seq
    if raw_id:
        sanitized = _TOOL_ID_CLEAN_RE.sub('_', raw_id)
        # Ensure the result has at least one alphanumeric character
        if sanitized and any(c.isalnum() for c in sanitized):
            return sanitized
    # Generate a unique fallback ID
    _tool_id_seq += 1
    safe_name = (_TOOL_ID_CLEAN_RE.sub('_', fallback_name) or "unknown")[:20]
    return f"toolu_{safe_name}_{_tool_id_seq}"


class AnthropicProvider(EnhancedProvider):
    """Enhanced provider adapter for Anthropic Claude models."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize Anthropic provider with enhanced features."""
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "anthropic"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate Anthropic API key is configured."""
        if not self.api_key:
            return False, "Anthropic API key not configured"
        return True, ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat with automatic retry, caching, and rate limiting.
        
        Features:
        - Automatic retry with exponential backoff
        - Integrated prompt caching from v3.17.11
        - Integrated MCP authentication
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

    @staticmethod
    def _split_system(messages: List[Dict[str, Any]]):
        """Split system messages and convert OpenAI-style tool messages to Anthropic format.
        
        Anthropic doesn't accept role="tool" messages. Tool results must be sent as:
        - User message with content=[{"type": "tool_result", "tool_use_id": ..., "content": ...}]
        
        This method:
        1. Extracts system messages into separate string
        2. Converts OpenAI assistant+tool_calls to Anthropic assistant+tool_use
        3. Converts OpenAI tool messages to Anthropic user+tool_result messages
        """
        import json as _json
        system = ""
        conv_msgs = []
        i = 0

        # Map original tool_call IDs → sanitized IDs so that tool_use and
        # tool_result blocks always reference the *same* Anthropic-safe ID.
        # Key = original ID string (may be ""), Value = sanitized ID.
        # When the original ID is empty we need positional disambiguation,
        # so we use a list of IDs generated from the most recent assistant
        # tool_calls block, consumed in order by the following tool messages.
        _tc_id_map: dict = {}        # original_id → sanitized_id
        _pending_tc_ids: list = []   # positional queue for empty-ID fallback

        while i < len(messages):
            m = messages[i]
            role = m.get("role", "")

            if role == "system":
                # Extract system content
                c = m.get("content", "")
                system += (c if isinstance(c, str) else "") + "\n"
                i += 1
            elif role == "assistant" and m.get("tool_calls"):
                # OpenAI format: assistant with tool_calls
                # Convert to Anthropic format: assistant with tool_use blocks
                text_content = m.get("content") or ""
                content_blocks = []
                if text_content:
                    content_blocks.append({"type": "text", "text": text_content})

                _pending_tc_ids = []  # reset queue for this assistant block
                for tc in m.get("tool_calls", []):
                    fn = tc.get("function", {})
                    args_str = fn.get("arguments", "{}")
                    try:
                        args = _json.loads(args_str) if isinstance(args_str, str) else args_str
                    except Exception:
                        args = {}
                    orig_id = tc.get("id", "") or ""
                    sanitized = _sanitize_tool_id(orig_id, fn.get("name", "unknown"))
                    # Store mapping so tool_result can look it up
                    if orig_id:
                        _tc_id_map[orig_id] = sanitized
                    _pending_tc_ids.append(sanitized)
                    content_blocks.append({
                        "type": "tool_use",
                        "id": sanitized,
                        "name": fn.get("name", ""),
                        "input": args,
                    })

                conv_msgs.append({"role": "assistant", "content": content_blocks})
                i += 1
            elif role == "tool":
                # OpenAI format: tool response message
                # Convert to Anthropic format: user message with tool_result
                # Re-use the same sanitized ID that was assigned to the tool_use
                def _resolve_tool_id(orig_id: str, fallback_name: str) -> str:
                    """Resolve a tool_call_id to its matching tool_use ID."""
                    if orig_id and orig_id in _tc_id_map:
                        return _tc_id_map[orig_id]
                    if _pending_tc_ids:
                        return _pending_tc_ids.pop(0)
                    # Last resort: generate a new sanitized ID
                    return _sanitize_tool_id(orig_id, fallback_name)

                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": _resolve_tool_id(m.get("tool_call_id", ""), m.get("name", "unknown")),
                    "content": m.get("content", ""),
                }
                # Collect consecutive tool messages into a single user message
                tool_results = [tool_result]
                i += 1
                while i < len(messages) and messages[i].get("role") == "tool":
                    next_tool = messages[i]
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": _resolve_tool_id(next_tool.get("tool_call_id", ""), next_tool.get("name", "unknown")),
                        "content": next_tool.get("content", ""),
                    })
                    i += 1

                conv_msgs.append({"role": "user", "content": tool_results})
            else:
                # Regular user/assistant message - keep as is
                conv_msgs.append(m)
                i += 1

        # Validate: ensure every user message with tool_result blocks is
        # preceded by an assistant message whose tool_use IDs match.
        # Drop orphaned tool_result user messages that would cause 400 errors.
        validated = []
        for idx, cm in enumerate(conv_msgs):
            content = cm.get("content", "")
            if cm.get("role") == "user" and isinstance(content, list):
                has_tool_result = any(
                    isinstance(c, dict) and c.get("type") == "tool_result"
                    for c in content
                )
                if has_tool_result:
                    # Check that the previous message is an assistant with matching tool_use IDs
                    if not validated:
                        logger.warning("Dropping orphaned tool_result at start of conversation")
                        continue
                    prev = validated[-1]
                    prev_content = prev.get("content", "")
                    if prev.get("role") == "assistant" and isinstance(prev_content, list):
                        prev_tool_use_ids = {
                            c.get("id") for c in prev_content
                            if isinstance(c, dict) and c.get("type") == "tool_use"
                        }
                        result_ids = {
                            c.get("tool_use_id") for c in content
                            if isinstance(c, dict) and c.get("type") == "tool_result"
                        }
                        if result_ids.issubset(prev_tool_use_ids):
                            validated.append(cm)
                        else:
                            logger.warning(
                                f"Dropping tool_result with mismatched IDs: "
                                f"result_ids={result_ids}, tool_use_ids={prev_tool_use_ids}"
                            )
                            # Also remove the preceding orphaned assistant+tool_use
                            if validated and prev.get("role") == "assistant":
                                _prev_has_only_tool_use = isinstance(prev_content, list) and all(
                                    isinstance(c, dict) and c.get("type") == "tool_use"
                                    for c in prev_content
                                )
                                if _prev_has_only_tool_use:
                                    validated.pop()
                    else:
                        logger.warning("Dropping tool_result not preceded by assistant+tool_use")
                    continue
            validated.append(cm)
        conv_msgs = validated

        return system.strip(), conv_msgs

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Actual Anthropic API call via SDK, with tool calling support."""
        import json as _json
        try:
            import anthropic as _anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed (pip install anthropic)")
        model = (self.model or "claude-3-5-haiku-20241022").replace("anthropic/", "")
        client = _anthropic.Anthropic(api_key=self.api_key)
        system, conv_msgs = self._split_system(messages)

        # Convert OpenAI tool schema format → Anthropic format
        # If tools are already in Anthropic format (from ToolRegistry), use directly.
        tool_schemas = self._get_intent_tools(intent_info)
        anthropic_tools = []
        for t in tool_schemas:
            if "function" in t:
                # OpenAI format → convert to Anthropic
                anthropic_tools.append({
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {"type": "object", "properties": {}}),
                })
            elif "name" in t and "input_schema" in t:
                # Already Anthropic format (from ToolRegistry AnthropicAdapter)
                anthropic_tools.append(t)

        _is_html_intent = bool(
            isinstance(intent_info, dict)
            and str(intent_info.get("intent", "")).lower() == "create_html_dashboard"
        )
        # claude-opus-4-6 supports 32k output tokens, claude-sonnet-4-6 supports 64k.
        # 8192 was a legacy limit for claude-3; raise the base to 32k so that large
        # Lovelace YAML rewrites (update_dashboard) don't get truncated mid-generation.
        # HTML dashboards get 64k to handle multi-chunk Vue/CSS payloads.
        _max_tokens = 65536 if _is_html_intent else 32768
        kwargs: Dict[str, Any] = {"model": model, "messages": conv_msgs, "max_tokens": _max_tokens}
        if system:
            kwargs["system"] = system
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        with client.messages.stream(**kwargs) as stream:
            text_chunks: List[str] = []
            for text in stream.text_stream:
                if text:
                    text_chunks.append(text)
                    yield {"type": "text", "text": text}
            final = stream.get_final_message()

        # Build done event
        done_event: Dict[str, Any] = {
            "type": "done",
            "finish_reason": getattr(final, "stop_reason", None) or "stop",
        }
        try:
            _u = getattr(final, "usage", None)
            logger.info(
                "anthropic: stream finished reason=%s (input=%s, output=%s, max_tokens=%s)",
                done_event["finish_reason"],
                getattr(_u, "input_tokens", 0) or 0,
                getattr(_u, "output_tokens", 0) or 0,
                _max_tokens,
            )
        except Exception:
            pass
        if getattr(final, "usage", None):
            done_event["usage"] = {
                "input_tokens": final.usage.input_tokens,
                "output_tokens": final.usage.output_tokens,
                "cache_read_input_tokens": getattr(final.usage, "cache_read_input_tokens", 0) or 0,
                "cache_creation_input_tokens": getattr(final.usage, "cache_creation_input_tokens", 0) or 0,
            }

        # Surface tool_use blocks as tool_calls for the api.py tool loop
        tool_calls = []
        for block in (getattr(final, "content", None) or []):
            if getattr(block, "type", "") == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": _json.dumps(block.input),
                })
        if tool_calls:
            done_event["tool_calls"] = self._normalize_tool_calls(
                tool_calls, tools=tool_schemas
            )
        elif text_chunks and tool_schemas:
            # Some models/providers may emit pseudo tool-calls as text
            # instead of tool_use blocks. Recover when possible.
            recovered = self._recover_tool_calls_from_text(
                "".join(text_chunks), tools=tool_schemas
            )
            if recovered:
                logger.info("anthropic: recovered %s tool_call(s) from text", len(recovered))
                done_event["tool_calls"] = recovered
                done_event["finish_reason"] = "tool_calls"

        yield done_event

    def get_available_models(self) -> List[str]:
        return [
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-4-5",
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-haiku-4-20250514",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get Anthropic-specific error translations."""
        return {
            "rate_limit": {
                "en": "Anthropic: Rate limit exceeded. Please retry in a moment.",
                "it": "Anthropic: Limite di velocità superato. Riprova tra poco.",
                "es": "Anthropic: Límite de velocidad excedido. Intenta de nuevo en un momento.",
                "fr": "Anthropic: Limite de vitesse dépassée. Réessayez dans un moment.",
            },
            "auth_error": {
                "en": "Anthropic: API key invalid or missing. Check your Anthropic API key in settings.",
                "it": "Anthropic: Chiave API non valida o mancante. Controlla le impostazioni.",
                "es": "Anthropic: Clave API inválida o faltante. Verifica la configuración.",
                "fr": "Anthropic: Clé API invalide ou manquante. Vérifiez les paramètres.",
            },
            "quota_exceeded": {
                "en": "Anthropic: Monthly API limit reached. Switch provider or wait for reset.",
                "it": "Anthropic: Limite mensile raggiunto. Cambia provider o attendi il reset.",
                "es": "Anthropic: Límite mensual alcanzado. Cambia de provider o espera el reset.",
                "fr": "Anthropic: Limite mensuelle atteinte. Changez de provider ou attendez le reset.",
            },
        }
