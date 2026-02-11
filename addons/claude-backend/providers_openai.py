"""OpenAI/GitHub/NVIDIA streaming providers for Home Assistant AI assistant."""

import json
import time
import logging
import requests

import api
import tools
import intent

logger = logging.getLogger(__name__)


def _is_request_too_large_error(err: Exception, error_msg: str) -> bool:
    status = getattr(err, "status_code", None)
    if status == 413:
        return True
    resp = getattr(err, "response", None)
    if resp is not None and getattr(resp, "status_code", None) == 413:
        return True
    msg = (error_msg or "").lower()
    return (
        "413" in msg
        or "tokens_limit_reached" in msg
        or "request body too large" in msg
        or "max size:" in msg and "tokens" in msg
    )


def _shrink_messages_for_small_limit(messages: list[dict], max_user_chars: int = 1600) -> bool:
    """Best-effort shrink of the prompt to fit small models like o4-mini.

    - Trim the message list further (keeping the most recent turns).
    - Remove injected smart-context blocks from the last user message.
    Returns True if any change was applied.
    """
    if not messages:
        return False

    changed = False

    # Trim history aggressively (tool pairs are handled by intent.trim_messages).
    try:
        trimmed = intent.trim_messages(messages, max_messages=10)
        # For github o4-mini we already reduce to 4 in intent.trim_messages; still guard here.
        if len(trimmed) < len(messages):
            messages[:] = trimmed
            changed = True
    except Exception:
        pass

    # Remove injected context from the last user message.
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if m.get("role") != "user" or not isinstance(m.get("content"), str):
            continue
        txt = m.get("content") or ""

        # If api.py injected smart context, drop it.
        for marker in ("\n\n---\nCONTESTO:\n", "\n\n---\nDATI:\n"):
            if marker in txt:
                txt = txt.split(marker, 1)[0].rstrip()
                txt += "\n\n[Nota: contesto ridotto automaticamente per limiti del modello selezionato.]"
                changed = True
                break

        if len(txt) > max_user_chars:
            txt = txt[:max_user_chars].rstrip() + "\n\n...[testo troncato per limiti del modello]"
            changed = True

        m["content"] = txt
        break

    return changed


def _is_rate_limit_error(err: Exception, error_msg: str) -> bool:
    """Return True if the exception looks like an HTTP 429 rate-limit.

    Important: do NOT match the substring 'rate' blindly (e.g. 'integrate').
    """
    status = getattr(err, "status_code", None)
    if status == 429:
        return True
    resp = getattr(err, "response", None)
    if resp is not None and getattr(resp, "status_code", None) == 429:
        return True
    msg = (error_msg or "").lower()
    return (
        "429" in msg
        or "too many requests" in msg
        or "rate limit" in msg
        or "ratelimit" in msg
    )


# ---- Helper functions (moved from api.py) ----

def _normalize_tool_args(args: object) -> str:
    """Return a stable string representation for tool-call arguments."""
    try:
        return json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        return str(args)


def _tool_signature(fn_name: str, args: object) -> str:
    return f"{fn_name}:{_normalize_tool_args(args)}"


def _github_model_variants(model: str) -> list[str]:
    """Return model identifier variants for GitHub Models runtime.

    GitHub's public catalog uses fully qualified IDs like 'openai/gpt-4o'.
    Some runtime configurations expect the short form (e.g., 'gpt-4o').
    We try both when we hit unknown_model.
    """
    if not model:
        return []
    variants = [model]
    if "/" in model:
        short = model.split("/", 1)[1]
        if short and short not in variants:
            variants.append(short)
    return variants


def _retry_with_swapped_max_token_param(kwargs: dict, max_tokens_value: int, api_err: Exception):
    """Retry once by swapping max_tokens/max_completion_tokens when API says it's unsupported."""
    error_msg = str(api_err)

    wants_max_completion = ("use 'max_completion_tokens'" in error_msg.lower())
    wants_max_tokens = ("use 'max_tokens'" in error_msg.lower())

    if not (wants_max_completion or wants_max_tokens):
        return None

    if wants_max_completion:
        kwargs.pop("max_tokens", None)
        kwargs["max_completion_tokens"] = max_tokens_value
        logger.warning("Retrying after unsupported_parameter: switching to max_completion_tokens")
    elif wants_max_tokens:
        kwargs.pop("max_completion_tokens", None)
        kwargs["max_tokens"] = max_tokens_value
        logger.warning("Retrying after unsupported_parameter: switching to max_tokens")

    return api.ai_client.chat.completions.create(**kwargs)


def _repair_tool_call_sequence(messages: list[dict]) -> bool:
    """Repair message history when an assistant tool_calls message is missing tool replies.

    OpenAI requires: assistant(role=assistant, tool_calls=[...]) MUST be followed by
    tool messages responding to each tool_call_id before the next user/assistant message.

    This can happen if a previous stream was aborted mid-round.
    Returns True if it modified the list.
    """
    if not messages:
        return False

    modified = False
    repaired: list[dict] = []
    pending: dict[str, bool] = {}

    def flush_pending():
        nonlocal modified
        if not pending:
            return
        for tool_call_id in list(pending.keys()):
            repaired.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps({
                    "error": "Missing tool response (auto-repaired). Please re-run the request if needed."
                }, ensure_ascii=False),
            })
            modified = True
        pending.clear()

    for m in messages:
        role = m.get("role")
        # If we see a non-tool message while tools are pending, we must close them.
        if pending and role != "tool":
            flush_pending()

        repaired.append(m)

        if role == "assistant" and m.get("tool_calls"):
            for tc in (m.get("tool_calls") or []):
                tc_id = (tc or {}).get("id")
                if isinstance(tc_id, str) and tc_id:
                    pending[tc_id] = True
        elif role == "tool":
            tc_id = m.get("tool_call_id")
            if isinstance(tc_id, str) and tc_id in pending:
                pending.pop(tc_id, None)

    # If conversation ends with pending tools, also flush.
    if pending:
        flush_pending()

    if modified:
        messages[:] = repaired
    return modified


def _safe_execute_tool(fn_name: str, args: dict) -> str:
    """Execute HA tool and never raise; returns a JSON string on errors."""
    try:
        return tools.execute_tool(fn_name, args)
    except Exception as e:
        logger.exception(f"Tool execution failed: {fn_name}: {e}")
        return json.dumps({"error": f"Tool '{fn_name}' failed: {str(e)}"}, ensure_ascii=False)


def _last_user_text(messages: list[dict]) -> str:
    for m in reversed(messages or []):
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            txt = m.get("content") or ""
            if txt.strip():
                return txt
    return ""


def _infer_search_query_from_messages(messages: list[dict]) -> str:
    """Infer a compact search query from recent user messages.
    This is used as a safety net for small-context models when they call search-like tools
    without providing arguments."""
    try:
        stop_words = set((api.KEYWORDS.get(api.LANGUAGE, {}) or {}).get("stop_words", []) or [])
    except Exception:
        stop_words = set()

    candidates: list[str] = []
    for m in reversed(messages or []):
        if m.get("role") != "user":
            continue
        text = m.get("content")
        if not isinstance(text, str):
            continue
        t = text.strip()
        if len(t) < 12:
            continue
        candidates.append(t)
        if len(candidates) >= 2:
            break

    if not candidates:
        t = _last_user_text(messages)
        candidates = [t] if t else []
    if not candidates:
        return ""

    text = candidates[0].lower()
    text = re.sub(r"[^a-z0-9àèéìòù\s._-]", " ", text)
    words = [w for w in text.split() if len(w) > 3 and w not in stop_words]
    if not words:
        return ""

    # Prefer longer/more specific tokens, keep short
    words = sorted(set(words), key=lambda w: (-len(w), w))
    return " ".join(words[:4])


def _normalize_entity_id_for_query_state(messages: list[dict], raw_entity_id: str) -> str:
    """Normalize entity_id for get_entity_state.

    If model passes a bare token like 'epcube' (no domain), we try search_entities
    and pick the best candidate using the query_state scoring.
    """
    if not raw_entity_id or not isinstance(raw_entity_id, str):
        return raw_entity_id
    if "." in raw_entity_id:
        return raw_entity_id

    try:
        search_raw = _safe_execute_tool("search_entities", {"query": raw_entity_id})
        items = json.loads(search_raw) if search_raw else []
    except Exception:
        items = []

    if not isinstance(items, list) or not items:
        return raw_entity_id

    user_msg = _last_user_text(messages)
    best = None
    best_score = -10**9
    for it in items:
        if not isinstance(it, dict) or not it.get("entity_id"):
            continue
        score = intent._score_query_state_candidate(user_msg, it.get("entity_id"), it.get("friendly_name") or "")
        if score > best_score:
            best_score = score
            best = it

    if best and best.get("entity_id") and best_score >= 20:
        fixed = best.get("entity_id")
        logger.warning(f"Normalized entity_id '{raw_entity_id}' -> '{fixed}' (score={best_score})")
        return fixed
    return raw_entity_id


# ---- NVIDIA Direct Streaming ----

def stream_chat_nvidia_direct(messages, intent_info=None):
    """Stream chat for NVIDIA using direct requests (not OpenAI SDK).
    This allows using NVIDIA-specific parameters like chat_template_kwargs for thinking mode."""
    trimmed = intent.trim_messages(messages)

    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools") is not None:
        system_prompt = intent.get_prompt_for_intent(intent_info)
        tool_defs = intent.get_tools_for_intent(intent_info, api.AI_PROVIDER)
        logger.info(f"NVIDIA focused mode: {intent_info['intent']} ({len(tool_defs)} tools)")
    else:
        system_prompt = tools.get_system_prompt()
        tool_defs = tools.get_openai_tools_for_provider()

    # Log available tools
    tool_names = [t.get("function", {}).get("name", "unknown") for t in tool_defs]
    logger.info(f"NVIDIA tools available ({len(tool_defs)}): {', '.join(tool_names)}")

    full_text = ""
    max_rounds = (intent_info or {}).get("max_rounds") or 5
    # Cache read-only tool results to avoid redundant calls
    tool_cache: dict[str, str] = {}
    read_only_tools = {
        "get_automations", "get_scripts", "get_dashboards",
        "get_dashboard_config", "read_config_file",
        "list_config_files", "get_frontend_resources",
        "search_entities", "get_entity_state", "get_entities",
    }

    for round_num in range(max_rounds):
        oai_messages = [{"role": "system", "content": system_prompt}] + intent.trim_messages(messages)

        # Prepare NVIDIA API request
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api.NVIDIA_API_KEY}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        }

        payload = {
            "model": api.get_active_model(),
            "messages": oai_messages,
            "max_tokens": 8192,
            "temperature": 0.7,
            "stream": True,
            "chat_template_kwargs": {"thinking": api.NVIDIA_THINKING_MODE}
        }
        # Only include tools if we have some
        if tool_defs:
            payload["tools"] = tool_defs

        logger.info(f"NVIDIA: Calling API with model={payload['model']}, thinking={api.NVIDIA_THINKING_MODE}, stream=True")

        try:
            # Increase timeout when thinking mode is enabled (reasoning takes longer)
            timeout_seconds = 300 if api.NVIDIA_THINKING_MODE else 120
            response = requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout_seconds)
            response.raise_for_status()
            logger.info("NVIDIA: Response stream started")

            # Parse SSE stream manually
            content_parts = []
            tool_calls_map = {}

            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.strip():
                    continue

                # SSE format: "data: {...}"
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix

                    if data.strip() == "[DONE]":
                        break

                    try:
                        chunk_data = json.loads(data)
                        if not chunk_data.get("choices"):
                            continue

                        delta = chunk_data["choices"][0].get("delta", {})

                        if delta.get("content"):
                            content_parts.append(delta["content"])

                        if delta.get("tool_calls"):
                            for tc_delta in delta["tool_calls"]:
                                idx = tc_delta.get("index", 0)
                                if idx not in tool_calls_map:
                                    tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                                if tc_delta.get("id"):
                                    tool_calls_map[idx]["id"] = tc_delta["id"]
                                if tc_delta.get("function"):
                                    if tc_delta["function"].get("name"):
                                        tool_calls_map[idx]["name"] = tc_delta["function"]["name"]
                                    if tc_delta["function"].get("arguments"):
                                        tool_calls_map[idx]["arguments"] += tc_delta["function"]["arguments"]

                    except json.JSONDecodeError:
                        continue

            accumulated = "".join(content_parts)

            if not tool_calls_map:
                # No tools - stream the final text
                full_text = accumulated
                low = (full_text or "").lower()
                is_confirmation_step = any(
                    p in low
                    for p in ("confermi", "scrivi sì o no", "scrivi si o no", "confirm", "confirme", "confirmer")
                )
                log_fn = logger.info if is_confirmation_step else logger.warning
                log_fn(f"OpenAI: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'"
                )
                is_confirmation_step = any(
                    p in low
                    for p in ("confermi", "scrivi sì o no", "scrivi si o no", "confirm", "confirme", "confirmer")
                )
                log_fn = logger.info if is_confirmation_step else logger.warning
                log_fn(f"NVIDIA: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'")
                messages.append({"role": "assistant", "content": full_text})
                yield {"type": "clear"}
                for i in range(0, len(full_text), 4):
                    chunk = full_text[i:i+4]
                    yield {"type": "token", "content": chunk}
                break

            # Build assistant message with tool calls
            logger.info(f"Round {round_num+1}: {len(tool_calls_map)} tool(s), skipping intermediate text")
            tc_list = []
            for idx in sorted(tool_calls_map.keys()):
                tc = tool_calls_map[idx]
                tc_list.append({
                    "id": tc["id"], "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]}
                })

            messages.append({"role": "assistant", "content": accumulated, "tool_calls": tc_list})

            # Execute tools (same logic as OpenAI)
            tool_call_results = {}
            for tc in tc_list:
                fn_name = tc["function"]["name"]
                args_str = tc["function"]["arguments"]
                tc_id = tc["id"]

                yield {"type": "tool_call", "name": fn_name, "arguments": args_str}

                try:
                    args = json.loads(args_str) if args_str.strip() else {}
                except json.JSONDecodeError:
                    result = json.dumps({"error": f"Invalid JSON arguments: {args_str}"})
                    tool_call_results[tc_id] = (fn_name, result)
                    continue

                # Normalize entity_id for query_state when model passes a bare token like 'epcube'
                if fn_name == "get_entity_state" and isinstance(args, dict):
                    raw_eid = args.get("entity_id")
                    if isinstance(raw_eid, str) and raw_eid and "." not in raw_eid:
                        args["entity_id"] = _normalize_entity_id_for_query_state(messages, raw_eid)

                sig = _tool_signature(fn_name, args)

                # Reuse cached results for read-only tools with identical args
                if fn_name in read_only_tools and sig in tool_cache:
                    logger.warning(f"Reusing cached tool result: {fn_name} {sig}")
                    result = tool_cache[sig]
                    tool_call_results[tc_id] = (fn_name, result)
                    yield {"type": "tool_result", "name": fn_name, "result": result}
                    continue

                # Execute tool using the standard execute_tool function
                logger.info(f"NVIDIA: Executing tool '{fn_name}' with args: {args}")
                result = _safe_execute_tool(fn_name, args)
                logger.info(f"NVIDIA: Tool '{fn_name}' returned {len(result)} chars: {result[:300]}...")

                if fn_name in read_only_tools:
                    tool_cache[sig] = result

                tool_call_results[tc_id] = (fn_name, result)
                yield {"type": "tool_result", "name": fn_name, "result": result}

            # Add tool results to messages
            for tc_id, (fn_name, result) in tool_call_results.items():
                messages.append({"role": "tool", "tool_call_id": tc_id, "name": fn_name, "content": result})

        except requests.HTTPError as e:
            status = e.response.status_code if getattr(e, "response", None) is not None else None
            error_msg = str(e)

            if status == 429 or _is_rate_limit_error(e, error_msg):
                logger.warning(f"NVIDIA rate limit hit at round {round_num+1}: {error_msg}")
                yield {"type": "status", "message": "Rate limit NVIDIA raggiunto, attendo..."}
                time.sleep(10)
                continue

            # 404 on /chat/completions is commonly returned when the model ID is not available for this key.
            if status == 404:
                bad_model = payload.get("model")
                if bad_model:
                    api.blocklist_nvidia_model(bad_model)
                logger.warning(f"NVIDIA model not available (404): {bad_model}")
                yield {"type": "status", "message": "⚠️ Modello NVIDIA non disponibile (404). L'ho rimosso dalla lista modelli."}
                error_msg_text = f"NVIDIA: modello non disponibile: {bad_model or 'unknown'}"
                messages.append({"role": "assistant", "content": error_msg_text})
                yield {"type": "clear"}
                yield {"type": "token", "content": error_msg_text}
                break

            logger.error(f"NVIDIA API HTTP error ({status}): {e}")
            error_msg_text = f"NVIDIA API error: {error_msg}"
            messages.append({"role": "assistant", "content": error_msg_text})
            yield {"type": "clear"}
            yield {"type": "token", "content": error_msg_text}
            break

        except Exception as e:
            error_msg_text = f"NVIDIA API error: {str(e)}"
            logger.error(error_msg_text)
            messages.append({"role": "assistant", "content": error_msg_text})
            yield {"type": "clear"}
            yield {"type": "token", "content": error_msg_text}
            break


# ---- OpenAI/GitHub Streaming ----

def stream_chat_openai(messages, intent_info=None):
    """Stream chat for OpenAI/GitHub with real token streaming. Yields SSE event dicts.
    Uses intent_info to select focused tools and prompt when available."""
    # Repair conversation state if a previous run was aborted mid tool-call.
    _repair_tool_call_sequence(messages)

    trimmed = intent.trim_messages(messages)

    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools") is not None:
        system_prompt = intent.get_prompt_for_intent(intent_info)
        tool_defs = intent.get_tools_for_intent(intent_info, api.AI_PROVIDER)
        logger.info(f"OpenAI focused mode: {intent_info['intent']} ({len(tool_defs)} tools)")
    else:
        system_prompt = tools.get_system_prompt()
        tool_defs = tools.get_openai_tools_for_provider()

    # Log available tools for debugging
    tool_names = [t.get("function", {}).get("name", "unknown") for t in tool_defs]
    logger.info(f"OpenAI tools available ({len(tool_defs)}): {', '.join(tool_names)}")

    max_tok = 4000 if api.AI_PROVIDER == "github" else 4096
    full_text = ""

    # FIX: max_rounds from intent_info, or 3 for GitHub (was 5), 5 for others
    max_rounds = (intent_info or {}).get("max_rounds") or (3 if api.AI_PROVIDER == "github" else 5)
    # Cache read-only tool results to avoid redundant calls (and reduce extra rounds / rate limits)
    tool_cache: dict[str, str] = {}

    read_only_tools = {
        "get_automations", "get_scripts", "get_dashboards",
        "get_dashboard_config", "read_config_file",
        "list_config_files", "get_frontend_resources",
        "search_entities", "get_entity_state", "get_entities",
    }

    for round_num in range(max_rounds):
        did_size_retry = False
        # Rate-limit prevention for GitHub Models: small delay before subsequent rounds
        if api.AI_PROVIDER == "github" and round_num > 0:
            delay = min(2 + round_num, 5)
            logger.info(f"Rate-limit prevention (GitHub): waiting {delay}s before round {round_num+1}")
            yield {"type": "status", "message": f"Rate limit GitHub: attendo {delay}s..."}
            time.sleep(delay)

        oai_messages = [{"role": "system", "content": system_prompt}] + intent.trim_messages(messages)

        # NVIDIA Kimi K2.5: configure thinking mode
        kwargs = {
            "model": api.get_active_model(),
            "messages": oai_messages,
            **api.get_max_tokens_param(max_tok),
            "stream": True
        }
        # Only include tools if we have some (empty list = no tools for chat intent)
        if tool_defs:
            kwargs["tools"] = tool_defs

        if api.AI_PROVIDER == "nvidia":
            kwargs["temperature"] = 0.7
            # Override with NVIDIA-specific max_tokens (always uses max_tokens, not max_completion_tokens)
            kwargs.pop("max_completion_tokens", None)  # Remove if present
            kwargs["max_tokens"] = 8192
            # NVIDIA can be slower, use longer timeout
            kwargs["timeout"] = 120.0

        logger.info(f"OpenAI: Calling API with model={kwargs['model']}, stream=True")
        try:
            response = api.ai_client.chat.completions.create(**kwargs)
        except Exception as api_err:
            error_msg = str(api_err)
            # Repair common invalid_request_error: missing tool messages after tool_calls
            if "tool_calls" in error_msg and "must be followed by tool messages" in error_msg:
                if _repair_tool_call_sequence(messages):
                    logger.warning("Repaired dangling tool_calls in history; retrying request once.")
                    yield {"type": "status", "message": "Ho riparato lo stato dei tool, riprovo..."}
                    response = api.ai_client.chat.completions.create(**kwargs)
                else:
                    raise
            if api.AI_PROVIDER == "github" and (
                "unsupported parameter" in error_msg.lower() or "unsupported_parameter" in error_msg.lower()
            ):
                try:
                    retry = _retry_with_swapped_max_token_param(kwargs, max_tok, api_err)
                    if retry is not None:
                        yield {"type": "status", "message": "Parametri token non compatibili col modello, riprovo."}
                        response = retry
                    else:
                        raise
                except Exception:
                    raise
            elif api.AI_PROVIDER == "github" and "unknown_model" in error_msg.lower():
                bad_model = kwargs.get("model")

                # Try alternate model formats first (e.g., 'openai/gpt-4o' -> 'gpt-4o')
                tried = []
                for candidate in _github_model_variants(bad_model):
                    if candidate in tried:
                        continue
                    tried.append(candidate)
                    if candidate == bad_model:
                        continue
                    try:
                        logger.warning(f"GitHub unknown_model for {bad_model}. Retrying with model={candidate}.")
                        yield {"type": "status", "message": "Modello GitHub non riconosciuto, riprovo con formato alternativo."}
                        kwargs["model"] = candidate
                        response = api.ai_client.chat.completions.create(**kwargs)
                        break
                    except Exception as retry_err:
                        if "unknown_model" in str(retry_err).lower():
                            continue
                        raise
                else:
                    # Still unknown after variants: blocklist canonical ID (the one shown in UI)
                    if bad_model:
                        api.GITHUB_MODEL_BLOCKLIST.add(bad_model)

                    # Final fallback attempts (both qualified and short)
                    fallback_candidates = ["openai/gpt-4o", "gpt-4o"]
                    for fallback_model in fallback_candidates:
                        if bad_model == fallback_model:
                            continue
                        try:
                            logger.warning(f"GitHub unknown_model: {bad_model}. Falling back to {fallback_model}.")
                            yield {"type": "status", "message": "Modello non disponibile su GitHub, passo a GPT-4o."}
                            kwargs["model"] = fallback_model
                            response = api.ai_client.chat.completions.create(**kwargs)
                            break
                        except Exception as fallback_err:
                            if "unknown_model" in str(fallback_err).lower():
                                continue
                            raise
                    else:
                        raise
            # FIX: Handle 429 rate limit errors with backoff (without matching 'integrate')
            elif _is_rate_limit_error(api_err, error_msg):
                logger.warning(f"Rate limit hit at round {round_num+1}: {error_msg}")
                yield {"type": "status", "message": "Rate limit raggiunto, attendo..."}
                time.sleep(10)
                continue  # Retry this round
            # Handle small-model prompt limits (e.g., GitHub o4-mini max request size)
            elif api.AI_PROVIDER == "github" and _is_request_too_large_error(api_err, error_msg) and not did_size_retry:
                did_size_retry = True
                logger.warning(f"Prompt too large for GitHub model={kwargs.get('model')}: {error_msg}")
                yield {"type": "status", "message": "Il modello selezionato ha un limite basso (prompt troppo grande). Riduco il contesto e riprovo..."}
                if _shrink_messages_for_small_limit(messages):
                    oai_messages = [{"role": "system", "content": system_prompt}] + intent.trim_messages(messages)
                    kwargs["messages"] = oai_messages
                response = api.ai_client.chat.completions.create(**kwargs)
            else:
                raise
        logger.info("OpenAI: Response stream started")

        content_parts = []
        tool_calls_map = {}

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if delta.content:
                content_parts.append(delta.content)

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.id:
                        tool_calls_map[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_map[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc_delta.function.arguments

        accumulated = "".join(content_parts)

        if not tool_calls_map:
            # No tools - stream the final text now
            full_text = accumulated
            logger.warning(f"OpenAI: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'")
            logger.info(f"OpenAI: This means the AI decided not to use any of the {len(tool_defs)} available tools")
            # Save assistant message to conversation
            messages.append({"role": "assistant", "content": full_text})
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                chunk = full_text[i:i+4]
                yield {"type": "token", "content": chunk}
            break

        # Build assistant message with tool calls
        logger.info(f"Round {round_num+1}: {len(tool_calls_map)} tool(s), skipping intermediate text")
        tc_list = []
        for idx in sorted(tool_calls_map.keys()):
            tc = tool_calls_map[idx]
            tc_list.append({
                "id": tc["id"], "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]}
            })

        messages.append({"role": "assistant", "content": accumulated, "tool_calls": tc_list})

        tool_call_results = {}  # Map tc_id -> (fn_name, result)
        for tc in tc_list:
            fn_name = tc["function"]["name"]

            # Parse args safely
            args_str = tc["function"].get("arguments") or "{}"
            try:
                args = json.loads(args_str) if args_str.strip() else {}
            except json.JSONDecodeError:
                args = {}

            # Safety net for GitHub small-context models: avoid huge get_automations payloads
            if api.AI_PROVIDER == "github" and fn_name == "get_automations" and isinstance(args, dict):
                if not args.get("query"):
                    inferred = _infer_search_query_from_messages(messages)
                    if inferred:
                        args["query"] = inferred
                        args.setdefault("limit", 10)

            # Normalize entity_id for query_state when model passes a bare token like 'epcube'
            if fn_name == "get_entity_state" and isinstance(args, dict):
                raw_eid = args.get("entity_id")
                if isinstance(raw_eid, str) and raw_eid and "." not in raw_eid:
                    args["entity_id"] = _normalize_entity_id_for_query_state(messages, raw_eid)

            sig = _tool_signature(fn_name, args)

            # Reuse cached results for read-only tools with identical args
            if fn_name in read_only_tools and sig in tool_cache:
                logger.warning(f"Reusing cached tool result: {fn_name} {sig}")
                result = tool_cache[sig]
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
                tool_call_results[tc["id"]] = (fn_name, result)
                continue

            # Execute tool
            yield {"type": "tool", "name": fn_name, "description": tools.get_tool_description(fn_name)}
            logger.info(f"OpenAI: Executing tool '{fn_name}' with args: {args}")
            result = _safe_execute_tool(fn_name, args)
            logger.info(f"OpenAI: Tool '{fn_name}' returned {len(result)} chars: {result[:300]}...")

            # Truncate large results to prevent token overflow
            max_len = 3000 if api.AI_PROVIDER == "github" else 8000
            if len(result) > max_len:
                result = result[:max_len] + '\n... [TRUNCATED - ' + str(len(result)) + ' chars total]'
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            tool_call_results[tc["id"]] = (fn_name, result)

            if fn_name in read_only_tools:
                tool_cache[sig] = result

        # AUTO-STOP: If a write tool succeeded, format response directly
        WRITE_TOOLS = {"update_automation", "update_script", "update_dashboard_card",
                   "create_automation", "create_script", "create_dashboard", "update_dashboard",
                   "write_config_file"}
        auto_stop = False
        for tc_id, (fn_name, result) in tool_call_results.items():
            if fn_name in WRITE_TOOLS:
                try:
                    rdata = json.loads(result)
                    if rdata.get("status") == "success":
                        auto_stop = True
                        full_text = api._format_write_tool_response(fn_name, rdata)
                        break
                except (json.JSONDecodeError, KeyError):
                    pass

        if auto_stop:
            logger.info(f"Auto-stop: write tool succeeded, skipping further API calls")
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                yield {"type": "token", "content": full_text[i:i+4]}
            break

        # AUTO-STOP (query_state): after gathering data, answer directly to avoid extra LLM rounds
        if intent_info and intent_info.get("intent") == "query_state":
            candidates = []
            # Pull candidates from tool results
            for _tc_id, (fn_name, result) in tool_call_results.items():
                if fn_name == "search_entities":
                    try:
                        items = json.loads(result)
                        if isinstance(items, list):
                            for it in items:
                                if isinstance(it, dict) and it.get("entity_id"):
                                    candidates.append({
                                        "entity_id": it.get("entity_id"),
                                        "friendly_name": it.get("friendly_name") or "",
                                    })
                    except Exception:
                        pass

            # If we found candidates, pick the best and fetch its state once
            if candidates:
                user_msg = ""
                # last user message is usually at the end
                for m in reversed(messages):
                    if m.get("role") == "user" and isinstance(m.get("content"), str):
                        user_msg = m.get("content")
                        break

                best = None
                best_score = -10**9
                for c in candidates:
                    s = intent._score_query_state_candidate(user_msg, c.get("entity_id"), c.get("friendly_name"))
                    if s > best_score:
                        best_score = s
                        best = c

                if best and best.get("entity_id") and best_score >= 20:
                    try:
                        state_json = tools.execute_tool("get_entity_state", {"entity_id": best["entity_id"]})
                        state_data = json.loads(state_json) if isinstance(state_json, str) else {}
                        full_text = intent._format_query_state_answer(best["entity_id"], state_data if isinstance(state_data, dict) else {})
                        logger.info("Auto-stop: query_state answered locally to avoid extra API call")
                        messages.append({"role": "assistant", "content": full_text})
                        yield {"type": "clear"}
                        for i in range(0, len(full_text), 4):
                            yield {"type": "token", "content": full_text[i:i+4]}
                        break
                    except Exception as e:
                        logger.warning(f"Auto-stop query_state failed: {e}")

    messages.append({"role": "assistant", "content": full_text})
    yield {"type": "done", "full_text": full_text}
