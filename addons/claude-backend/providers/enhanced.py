"""Enhanced provider base with integrated caching, auth, and error handling.

This extends the basic BaseProvider with v3.17.11+ features:
- Prompt caching integration
- MCP custom auth support
- Unified error handling and translations
- Automatic retry logic
- Performance statistics
"""

import json
import logging
import time
from abc import abstractmethod
from typing import Any, Dict, Optional, Generator, List

import httpx

from .base import BaseProvider
from prompt_caching import get_cache_manager
from mcp_auth import get_mcp_auth_manager

logger = logging.getLogger(__name__)


class EnhancedProvider(BaseProvider):
    """Enhanced provider base with v3.17.11+ enterprise features.

    === PROVIDER CONTRACT ===
    To add a new OpenAI-compatible provider, subclass this and set class attributes:

        class MyProvider(EnhancedProvider):
            BASE_URL      = "https://api.example.com/v1"  # required
            DEFAULT_MODEL = "my-model"                    # required
            INCLUDE_USAGE = True   # False if API rejects stream_options
            EXTRA_HEADERS = {}     # any extra HTTP headers (e.g. User-Agent)

            @staticmethod
            def get_provider_name(): return "example"

            def validate_credentials(self):
                return (True, "") if self.api_key else (False, "API key missing")

            def get_available_models(self):
                return ["my-model", "my-model-v2"]

        # OPTIONAL overrides:
        #   _prepare_messages(messages, intent_info) → List
        #       Default: inject intent system prompt. Override to add sanitization.
        #   _get_model() → str
        #       Default: self.model or self.DEFAULT_MODEL. Override for model renaming.

        # That's it. Tool calling, intent handling, conversation history,
        # smart context pre-loading, and cost tracking are all automatic.
    =========================
    """

    # --- Class attributes for the standard OpenAI-compatible implementation ---
    # Subclasses set these instead of overriding _do_stream().
    BASE_URL: str = ""        # API base URL  (e.g. "https://api.mistral.ai/v1")
    DEFAULT_MODEL: str = ""   # Fallback model when self.model is empty
    INCLUDE_USAGE: bool = True  # Set False if provider rejects stream_options
    EXTRA_HEADERS: Dict[str, str] = {}  # Additional HTTP headers

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize enhanced provider."""
        super().__init__(api_key, model)
        self.cache_manager = get_cache_manager()
        self.auth_manager = get_mcp_auth_manager()
        self.stats = {
            "requests": 0,
            "failures": 0,
            "retries": 0,
            "cache_hits": 0,
            "total_tokens": 0,
        }
        self.last_error = ""
        self.last_error_time = 0.0

    def stream_chat_with_caching(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat with automatic retries and caching integration.
        
        Args:
            messages: Conversation messages
            intent_info: Intent information for caching decisions
            max_retries: Maximum number of retries on failure
            
        Yields:
            Standard event dictionaries
        """
        intent_name = (intent_info or {}).get("intent", "")
        retry_count = 0
        last_exception = None

        while retry_count <= max_retries:
            try:
                self.stats["requests"] += 1

                # Check if we should use caching for this request
                if self.cache_manager.should_cache_intent(intent_name):
                    logger.debug(f"{self.name}: Caching enabled for intent '{intent_name}'")

                # Stream the chat (calls _do_stream, NOT stream_chat, to avoid recursion)
                for event in self._do_stream(messages, intent_info):
                    # Record cache usage if present
                    if event.get("type") == "done" and event.get("usage"):
                        self._record_cache_usage(event.get("usage"), intent_name)

                    yield event

                # Success - exit retry loop
                return

            except Exception as e:
                last_exception = e
                error_msg = str(e)
                logger.warning(
                    f"{self.name}: Request failed (attempt {retry_count + 1}/{max_retries + 1}): {error_msg}"
                )

                self.stats["failures"] += 1
                self.last_error = error_msg
                self.last_error_time = time.time()

                # Check if we should retry
                if self._should_retry_error(error_msg) and retry_count < max_retries:
                    self.stats["retries"] += 1
                    retry_count += 1

                    # Exponential backoff
                    wait_time = (2 ** retry_count) * 0.5
                    logger.info(f"{self.name}: Retrying after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Don't retry - yield error
                    yield self._format_event(
                        "error",
                        message=self.normalize_error_message(e)
                    )
                    return

        # All retries exhausted
        if last_exception:
            yield self._format_event(
                "error",
                message=f"{self.name} failed after {max_retries + 1} attempts: {self.normalize_error_message(last_exception)}"
            )

    @staticmethod
    def _inject_intent_system_prompt(
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Prepend (or merge) an intent-specific system message into the messages list.

        Used by OpenAI-compatible providers (Mistral, Groq, DeepSeek, …) that call
        _openai_compat_stream directly and have no separate system-prompt parameter.
        For web providers (claude_web, chatgpt_web) this is handled inside stream_chat.
        """
        intent_name = (intent_info or {}).get("intent", "")

        if intent_name == "create_html_dashboard":
            system_text = (
                "You are a creative Home Assistant HTML dashboard designer.\n"
                "The user wants a UNIQUE, beautiful STANDALONE HTML page — NOT YAML, NOT a Lovelace card.\n\n"
                "MANDATORY RULES — VIOLATION IS NOT ALLOWED:\n"
                "• Output a COMPLETE <!DOCTYPE html>...</html> page wrapped in ```html ... ```\n"
                "• YOUR FIRST LINE OF OUTPUT MUST BE: ```html\n"
                "• NEVER output YAML, 'vertical-stack', 'type: entities', 'type: custom:', "
                "  or ANY Lovelace / Home Assistant card format\n"
                "• Do NOT produce JSON, markdown lists, or explanatory text — ONLY the HTML block\n"
                "• Use a modern dark design with CSS animations, gradients, and card-based layout\n"
                "• Poll HA states via: fetch('/api/states/ENTITY_ID', {headers:{Authorization:'Bearer '+tok}})\n"
                "  where tok = JSON.parse(localStorage.getItem('hassTokens')||'{}').access_token || ''\n"
                "• Refresh every 5 seconds with setInterval\n"
                "• Include ALL the entity_ids provided in the CONTEXT section of the user message\n"
                "• The HTML is automatically saved — no tool call, no explanation needed\n"
            )
        else:
            system_text = (intent_info or {}).get("prompt", "")

        if not system_text:
            return messages

        # Merge into existing system message or prepend a new one
        if messages and messages[0].get("role") == "system":
            merged = system_text + "\n\n" + (messages[0].get("content") or "")
            return [{"role": "system", "content": merged}] + messages[1:]
        return [{"role": "system", "content": system_text}] + messages

    def _prepare_messages(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Prepare messages before sending to the API.

        Default: inject the intent system prompt (from intent_info["prompt"]).
        Override in subclasses for provider-specific preprocessing
        (e.g. Groq needs to flatten Anthropic list-content blocks to plain text).

        Always call super()._prepare_messages() to keep the base behaviour.
        """
        return self._inject_intent_system_prompt(list(messages), intent_info)

    def _get_model(self) -> str:
        """Return the model identifier to use for the API call.

        Default: self.model (user setting) falling back to DEFAULT_MODEL.
        Override to rename/strip prefixes (e.g. GitHub strips 'openai/').
        """
        return self.model or self.DEFAULT_MODEL

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Standard OpenAI-compatible streaming implementation.

        Uses BASE_URL, DEFAULT_MODEL, INCLUDE_USAGE, EXTRA_HEADERS class
        attributes plus _prepare_messages() and _get_model() hooks.

        Providers that inherit from EnhancedProvider and set those class
        attributes do NOT need to override this method — it just works.

        For non-OpenAI-compatible APIs (e.g. Anthropic SDK) override this
        method with the provider-specific implementation.
        """
        if not self.BASE_URL:
            raise NotImplementedError(
                f"{self.name}: Set BASE_URL class attribute or override _do_stream().\n"
                "See the PROVIDER CONTRACT in EnhancedProvider docstring."
            )
        msgs = self._prepare_messages(messages, intent_info)
        tools = self._get_intent_tools(intent_info) or None
        yield from self._openai_compat_stream(
            self.BASE_URL,
            self.api_key,
            self._get_model(),
            msgs,
            tools=tools,
            extra_headers=self.EXTRA_HEADERS or None,
            include_usage=self.INCLUDE_USAGE,
        )

    @staticmethod
    def _get_intent_tools(intent_info: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract OpenAI-format tool schemas from intent_info['tool_schemas'].

        Called by provider _do_stream methods to get the tool list to pass
        to the API. Returns empty list if no tools are available.
        """
        return (intent_info or {}).get("tool_schemas") or []

    @staticmethod
    def _openai_compat_stream(
        base_url: str,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        include_usage: bool = True,
    ) -> Generator[Dict[str, Any], None, None]:
        """Shared streaming helper for OpenAI-compatible REST APIs.

        Works with OpenAI, NVIDIA NIM, Groq, Mistral, and any provider that
        speaks the OpenAI chat-completions SSE protocol.

        When `tools` is provided, it is included in the request body and
        tool_call deltas are accumulated and returned as part of the done event:
            {"type": "done", "finish_reason": "tool_calls", "tool_calls": [...]}
        The caller (api.py tool loop) is responsible for executing the tool calls
        and continuing the conversation.
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        if extra_headers:
            headers.update(extra_headers)
        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if include_usage:
            body["stream_options"] = {"include_usage": True}
        if tools:
            body["tools"] = tools
        url = base_url.rstrip("/") + "/chat/completions"
        captured_usage: Optional[Dict[str, Any]] = None
        # Accumulate streaming tool_call fragments keyed by index
        accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}
        # connect=10s: fallisce subito se il server non risponde
        # read=120s: i modelli grandi (DeepSeek, Llama 405B) sono lenti ma streamano
        # pool/write standard
        _timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=5.0)
        with httpx.stream("POST", url, headers=headers, json=body, timeout=_timeout) as response:
            if response.status_code != 200:
                error_text = response.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"HTTP {response.status_code}: {error_text[:400]}")
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str or data_str == "[DONE]":
                    if data_str == "[DONE]":
                        done_event: Dict[str, Any] = {"type": "done", "finish_reason": "stop"}
                        if captured_usage:
                            done_event["usage"] = captured_usage
                        if accumulated_tool_calls:
                            done_event["tool_calls"] = list(accumulated_tool_calls.values())
                        yield done_event
                    continue
                try:
                    event = json.loads(data_str)
                    # Some providers (e.g. Groq) embed errors inside the SSE stream
                    # as {"error": {"message": "...", "type": "..."}} instead of an
                    # HTTP error status. Silently skipping these causes HTTP 200 with
                    # no text in the UI. Detect and surface them explicitly.
                    if "error" in event and "choices" not in event:
                        err = event["error"]
                        msg = (
                            err.get("message")
                            or err.get("msg")
                            or str(err)
                        ) if isinstance(err, dict) else str(err)
                        yield {"type": "error", "message": msg}
                        return
                    # Capture usage data — present in last chunk (or a usage-only chunk
                    # with empty choices when stream_options.include_usage is set).
                    if event.get("usage"):
                        captured_usage = event["usage"]
                    choices = event.get("choices", [])
                    if not choices:
                        continue
                    choice = choices[0]
                    delta = choice.get("delta") or {}

                    # Accumulate tool_call fragments (each chunk adds a piece per index)
                    for tc in (delta.get("tool_calls") or []):
                        idx = tc.get("index", 0)
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": tc.get("id", ""),
                                "name": "",
                                "arguments": "",
                            }
                        if tc.get("id"):
                            accumulated_tool_calls[idx]["id"] = tc["id"]
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            accumulated_tool_calls[idx]["name"] += fn["name"]
                        accumulated_tool_calls[idx]["arguments"] += fn.get("arguments", "")

                    content = delta.get("content")
                    if content:
                        yield {"type": "text", "text": content}
                    finish = choice.get("finish_reason")
                    if finish:
                        done_event = {"type": "done", "finish_reason": finish}
                        if captured_usage:
                            done_event["usage"] = captured_usage
                        if finish == "tool_calls" and accumulated_tool_calls:
                            done_event["tool_calls"] = list(accumulated_tool_calls.values())
                        yield done_event
                except json.JSONDecodeError:
                    continue

    def _should_retry_error(self, error_msg: str) -> bool:
        """Determine if error is retryable.
        
        Retryable errors:
        - Rate limits (429)
        - Timeouts
        - Server errors (5xx)
        - Temporary network issues
        
        Non-retryable:
        - Auth errors (401, 403)
        - Invalid requests (400)
        - Quota exceeded
        """
        msg = (error_msg or "").lower()

        # Never retry auth/billing/config errors (permanent failures)
        if (
            self._is_auth_error(msg)
            or "insufficient_quota" in msg
            or "exceeded your current quota" in msg
            or "quota esaurita" in msg
            or "resource_exhausted" in msg
            or "billing" in msg
            or "invalid" in msg
            or "not found" in msg
        ):
            return False

        # Retry transient errors
        if (
            self._is_rate_limit_error(msg)
            or "timeout" in msg
            or "connection" in msg
            or "500" in msg
            or "502" in msg
            or "503" in msg
        ):
            return True

        return False

    def _record_cache_usage(self, usage: Dict[str, Any], intent_name: str):
        """Record cache usage statistics."""
        cache_read = usage.get("cache_read_input_tokens", 0) or 0
        cache_created = usage.get("cache_creation_input_tokens", 0) or 0
        output_tokens = usage.get("output_tokens", 0) or 0

        if cache_read > 0:
            self.stats["cache_hits"] += 1
            self.cache_manager.record_cache_usage(
                cache_read_input_tokens=cache_read,
                cache_creation_input_tokens=0,
                output_tokens=output_tokens,
                model=self.model
            )
            logger.info(
                f"{self.name}: Cache hit! {cache_read} tokens from cache (intent={intent_name})"
            )

        if cache_created > 0:
            self.cache_manager.record_cache_usage(
                cache_read_input_tokens=0,
                cache_creation_input_tokens=cache_created,
                output_tokens=output_tokens,
                model=self.model
            )
            logger.info(
                f"{self.name}: Cache write {cache_created} tokens (intent={intent_name})"
            )

        self.stats["total_tokens"] += (cache_read + cache_created + output_tokens)

    def get_auth_headers(self, mcp_server_name: Optional[str] = None) -> Dict[str, str]:
        """Get authentication headers for MCP server if configured.
        
        Args:
            mcp_server_name: MCP server name to get headers for
            
        Returns:
            Dictionary of auth headers (empty if no MCP auth configured)
        """
        if not mcp_server_name:
            return {}

        try:
            return self.auth_manager.get_headers_for_server(mcp_server_name)
        except KeyError:
            logger.debug(f"{self.name}: MCP server '{mcp_server_name}' not configured")
            return {}

    def get_statistics(self) -> Dict[str, Any]:
        """Get provider statistics."""
        total_requests = self.stats["requests"]
        success_rate = (
            (total_requests - self.stats["failures"]) / total_requests * 100
            if total_requests > 0
            else 0
        )

        return {
            "provider": self.name,
            "model": self.model,
            "requests": self.stats["requests"],
            "failures": self.stats["failures"],
            "retries": self.stats["retries"],
            "cache_hits": self.stats["cache_hits"],
            "total_tokens": self.stats["total_tokens"],
            "success_rate": f"{success_rate:.1f}%",
            "last_error": self.last_error,
            "last_error_time": self.last_error_time,
        }

    def reset_statistics(self):
        """Reset provider statistics."""
        self.stats = {
            "requests": 0,
            "failures": 0,
            "retries": 0,
            "cache_hits": 0,
            "total_tokens": 0,
        }
        self.last_error = ""
        self.last_error_time = 0.0
        logger.info(f"{self.name}: Statistics reset")

    # Error translation methods for common providers
    @staticmethod
    def get_error_translations() -> Dict[str, Dict[str, str]]:
        """Get provider-specific error translations.
        
        Override in subclasses for provider-specific translations.
        """
        return {
            "auth": {
                "en": "Authentication failed. Check your API key.",
                "it": "Autenticazione fallita. Controlla la tua API key.",
                "es": "Fallo en la autenticación. Verifica tu clave de API.",
                "fr": "L'authentification a échoué. Vérifiez votre clé API.",
            },
            "rate_limit": {
                "en": "Rate limit exceeded. Please retry in a moment.",
                "it": "Limite di velocità superato. Riprova tra poco.",
                "es": "Límite de velocidad excedido. Reintenta en un momento.",
                "fr": "Limite de débit dépassée. Réessayez dans un moment.",
            },
            "quota": {
                "en": "Usage quota exceeded. Upgrade your plan or retry later.",
                "it": "Quota di utilizzo superata. Aggiorna il tuo piano o riprova più tardi.",
                "es": "Cuota de uso excedida. Actualiza tu plan o reintenta más tarde.",
                "fr": "Quota d'utilisation dépassé. Mettez à jour votre plan ou réessayez plus tard.",
            },
            "server_error": {
                "en": "Server error. Please retry.",
                "it": "Errore del server. Riprova.",
                "es": "Error del servidor. Reintenta.",
                "fr": "Erreur du serveur. Réessayez.",
            },
            "invalid_request": {
                "en": "Invalid request. Check your input.",
                "it": "Richiesta non valida. Controlla il tuo input.",
                "es": "Solicitud no válida. Verifica tu entrada.",
                "fr": "Demande invalide. Vérifiez votre saisie.",
            },
        }
