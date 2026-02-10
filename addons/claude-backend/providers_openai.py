"""OpenAI/GitHub/NVIDIA streaming providers for Home Assistant AI assistant."""

import json
import time
import logging
import requests

import api
from tools import (get_system_prompt, get_openai_tools_for_provider, get_tool_description,
                   execute_tool)
from intent import (get_tools_for_intent, get_prompt_for_intent, trim_messages,
                    _score_query_state_candidate, _format_query_state_answer)

logger = logging.getLogger(__name__)


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


# ---- NVIDIA Direct Streaming ----

def stream_chat_nvidia_direct(messages, intent_info=None):
    """Stream chat for NVIDIA using direct requests (not OpenAI SDK).
    This allows using NVIDIA-specific parameters like chat_template_kwargs for thinking mode."""
    trimmed = trim_messages(messages)

    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools") is not None:
        system_prompt = get_prompt_for_intent(intent_info)
        tools = get_tools_for_intent(intent_info, api.AI_PROVIDER)
        logger.info(f"NVIDIA focused mode: {intent_info['intent']} ({len(tools)} tools)")
    else:
        system_prompt = get_system_prompt()
        tools = get_openai_tools_for_provider()

    # Log available tools
    tool_names = [t.get("function", {}).get("name", "unknown") for t in tools]
    logger.info(f"NVIDIA tools available ({len(tools)}): {', '.join(tool_names)}")

    full_text = ""
    max_rounds = (intent_info or {}).get("max_rounds") or 5
    tools_called_this_session = set()

    for round_num in range(max_rounds):
        oai_messages = [{"role": "system", "content": system_prompt}] + trim_messages(messages)

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
        if tools:
            payload["tools"] = tools

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
                logger.warning(f"NVIDIA: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'")
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
                if fn_name in tools_called_this_session:
                    logger.info(f"Skipping already-called tool: {fn_name}")
                    continue

                tools_called_this_session.add(fn_name)
                args_str = tc["function"]["arguments"]
                tc_id = tc["id"]

                yield {"type": "tool_call", "name": fn_name, "arguments": args_str}

                try:
                    args = json.loads(args_str) if args_str.strip() else {}
                except json.JSONDecodeError:
                    result = json.dumps({"error": f"Invalid JSON arguments: {args_str}"})
                    tool_call_results[tc_id] = (fn_name, result)
                    continue

                # Execute tool using the standard execute_tool function
                logger.info(f"NVIDIA: Executing tool '{fn_name}' with args: {args}")
                result = execute_tool(fn_name, args)
                logger.info(f"NVIDIA: Tool '{fn_name}' returned {len(result)} chars: {result[:300]}...")

                tool_call_results[tc_id] = (fn_name, result)
                yield {"type": "tool_result", "name": fn_name, "result": result}

            # Add tool results to messages
            for tc_id, (fn_name, result) in tool_call_results.items():
                messages.append({"role": "tool", "tool_call_id": tc_id, "name": fn_name, "content": result})

        except Exception as e:
            error_msg = str(e)
            # FIX: Handle 429 rate limit errors with backoff
            if "429" in error_msg or "rate" in error_msg.lower():
                logger.warning(f"NVIDIA rate limit hit at round {round_num+1}: {error_msg}")
                yield {"type": "status", "message": "Rate limit raggiunto, attendo..."}
                time.sleep(10)
                continue
            logger.error(f"NVIDIA API error: {e}")
            error_msg_text = f"NVIDIA API error: {str(e)}"
            messages.append({"role": "assistant", "content": error_msg_text})
            yield {"type": "clear"}
            yield {"type": "token", "content": error_msg_text}
            break


# ---- OpenAI/GitHub Streaming ----

def stream_chat_openai(messages, intent_info=None):
    """Stream chat for OpenAI/GitHub with real token streaming. Yields SSE event dicts.
    Uses intent_info to select focused tools and prompt when available."""
    trimmed = trim_messages(messages)

    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools") is not None:
        system_prompt = get_prompt_for_intent(intent_info)
        tools = get_tools_for_intent(intent_info, api.AI_PROVIDER)
        logger.info(f"OpenAI focused mode: {intent_info['intent']} ({len(tools)} tools)")
    else:
        system_prompt = get_system_prompt()
        tools = get_openai_tools_for_provider()

    # Log available tools for debugging
    tool_names = [t.get("function", {}).get("name", "unknown") for t in tools]
    logger.info(f"OpenAI tools available ({len(tools)}): {', '.join(tool_names)}")

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
        # Rate-limit prevention for GitHub Models: small delay before subsequent rounds
        if api.AI_PROVIDER == "github" and round_num > 0:
            delay = min(2 + round_num, 5)
            logger.info(f"Rate-limit prevention (GitHub): waiting {delay}s before round {round_num+1}")
            yield {"type": "status", "message": f"Rate limit GitHub: attendo {delay}s..."}
            time.sleep(delay)

        oai_messages = [{"role": "system", "content": system_prompt}] + trim_messages(messages)

        # NVIDIA Kimi K2.5: configure thinking mode
        kwargs = {
            "model": api.get_active_model(),
            "messages": oai_messages,
            **api.get_max_tokens_param(max_tok),
            "stream": True
        }
        # Only include tools if we have some (empty list = no tools for chat intent)
        if tools:
            kwargs["tools"] = tools

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
            # FIX: Handle 429 rate limit errors with backoff (was missing!)
            elif "429" in error_msg or "rate" in error_msg.lower():
                logger.warning(f"Rate limit hit at round {round_num+1}: {error_msg}")
                yield {"type": "status", "message": "Rate limit raggiunto, attendo..."}
                time.sleep(10)
                continue  # Retry this round
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
            logger.info(f"OpenAI: This means the AI decided not to use any of the {len(tools)} available tools")
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

            sig = _tool_signature(fn_name, args)

            # Reuse cached results for read-only tools with identical args
            if fn_name in read_only_tools and sig in tool_cache:
                logger.warning(f"Reusing cached tool result: {fn_name} {sig}")
                result = tool_cache[sig]
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
                tool_call_results[tc["id"]] = (fn_name, result)
                continue

            # Execute tool
            yield {"type": "tool", "name": fn_name, "description": get_tool_description(fn_name)}
            logger.info(f"OpenAI: Executing tool '{fn_name}' with args: {args}")
            result = execute_tool(fn_name, args)
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
                       "create_automation", "create_script", "create_dashboard", "update_dashboard"}
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
                    s = _score_query_state_candidate(user_msg, c.get("entity_id"), c.get("friendly_name"))
                    if s > best_score:
                        best_score = s
                        best = c

                if best and best.get("entity_id") and best_score >= 20:
                    try:
                        state_json = execute_tool("get_entity_state", {"entity_id": best["entity_id"]})
                        state_data = json.loads(state_json) if isinstance(state_json, str) else {}
                        full_text = _format_query_state_answer(best["entity_id"], state_data if isinstance(state_data, dict) else {})
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
