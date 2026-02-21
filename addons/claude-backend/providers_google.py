"""Google Gemini streaming provider for Home Assistant AI assistant."""

import json
import time
import logging

import api
import tools

logger = logging.getLogger(__name__)


def _is_rate_limit_error(error_msg: str) -> bool:
    """Return True if error message indicates rate limiting."""
    msg = (error_msg or "").lower()
    return (
        "429" in msg
        or "too many requests" in msg
        or "rate limit" in msg
        or "ratelimit" in msg
        or "resource_exhausted" in msg
    )


def _humanize_google_error(error_msg: str) -> str:
    """Return a user-friendly message for common Google API errors."""
    low = (error_msg or "").lower()

    if "api key not valid" in low or "api_key_invalid" in low or "invalid api key" in low:
        return api.tr("err_api_key_not_configured", provider_name="Google")
    if "quota" in low or "billing" in low:
        return {
            "en": "Google: API quota exceeded or billing not enabled. Check your Google Cloud project.",
            "it": "Google: quota API esaurita o fatturazione non attiva. Controlla il tuo progetto Google Cloud.",
            "es": "Google: cuota de API superada o facturación no habilitada. Revisa tu proyecto Google Cloud.",
            "fr": "Google: quota API dépassée ou facturation non activée. Vérifiez votre projet Google Cloud.",
        }.get(api.LANGUAGE, "Google: API quota exceeded. Check your Google Cloud project.")
    return {
        "en": "Google API error. Please retry or switch provider.",
        "it": "Errore Google API. Riprova oppure cambia provider.",
        "es": "Error de Google API. Reintenta o cambia de proveedor.",
        "fr": "Erreur Google API. Réessayez ou changez de fournisseur.",
    }.get(api.LANGUAGE, "Google API error. Please retry or switch provider.")


def _safe_execute_tool(fn_name: str, args: dict) -> str:
    """Execute HA tool and never raise; returns a JSON string on errors."""
    try:
        return tools.execute_tool(fn_name, args)
    except Exception as e:
        logger.exception(f"Tool execution failed: {fn_name}: {e}")
        return json.dumps({"error": f"Tool '{fn_name}' failed: {str(e)}"}, ensure_ascii=False)


def stream_chat_google(messages, intent_info: dict | None = None):
    """Stream chat for Google Gemini with tool events.
    Aligned with OpenAI/Anthropic providers: focused mode, auto-stop,
    tool result truncation, rate limit retry, redundancy detection, abort."""
    from google.genai import types

    provider_label = "Google"
    MAX_ROUNDS = 10

    # WRITE_TOOLS auto-stop: after these tools succeed, format response directly
    WRITE_TOOLS = {"update_automation", "update_script", "update_dashboard_card",
                   "create_automation", "create_script", "create_dashboard", "update_dashboard",
                   "create_html_dashboard", "write_config_file"}

    # Read-only tools — cache results to prevent redundant calls
    READ_ONLY_TOOLS = {"get_automations", "get_scripts", "get_dashboards",
                       "get_dashboard_config", "read_config_file",
                       "list_config_files", "get_frontend_resources",
                       "search_entities", "get_entity_state"}

    # Tool result truncation thresholds
    READ_TOOLS_LARGE = {"read_config_file", "get_entity_details", "get_entity_history"}

    def _to_parts(content: object) -> list[dict]:
        if isinstance(content, str):
            return [{"text": content}]
        if isinstance(content, list):
            parts: list[dict] = []
            for p in content:
                if isinstance(p, str):
                    parts.append({"text": p})
                elif isinstance(p, dict):
                    if "text" in p:
                        parts.append({"text": p.get("text")})
                    elif "inline_data" in p:
                        parts.append({"inline_data": p.get("inline_data")})
            return [pt for pt in parts if pt]
        return []

    contents: list[object] = []
    for m in messages:
        role = m.get("role")
        if role == "assistant":
            role = "model"
        if role not in ("user", "model"):
            continue
        parts = _to_parts(m.get("content"))
        if parts:
            contents.append({"role": role, "parts": parts})

    # Build tool config — use intent_info for focused mode if available
    gemini_tool = tools.get_gemini_tools(intent_info=intent_info)

    # Build system prompt with intent-specific prompt if available
    system_prompt = tools.get_system_prompt()
    if intent_info and intent_info.get("prompt"):
        system_prompt = intent_info["prompt"] + "\n\n" + system_prompt

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[gemini_tool],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    response = None
    round_num = 0
    rate_limit_retries = 0  # Separate counter to cap rate-limit retries regardless of round_num
    MAX_RATE_LIMIT_RETRIES = 3
    tool_cache: dict[str, str] = {}  # sig -> result (for redundancy detection)
    total_input_tokens = 0
    total_output_tokens = 0

    while round_num < MAX_ROUNDS:
        # Check abort flag
        if api.abort_streams.get("default"):
            logger.info("Google: Stream aborted by user")
            yield {"type": "error", "message": api.tr("status_user_cancelled")}
            api.abort_streams["default"] = False
            return

        # Rate-limit prevention: progressive delay between rounds (not on first)
        if round_num > 0:
            delay = min(2 + round_num, 5)  # 3s, 4s, 5s, 5s...
            logger.info(f"Google: Rate-limit prevention: waiting {delay}s before round {round_num+1}")
            yield {"type": "status", "message": api.tr("status_rate_limit_wait_seconds", provider=provider_label, seconds=delay)}
            time.sleep(delay)
            # Re-check abort after delay
            if api.abort_streams.get("default"):
                logger.info("Google: Stream aborted by user during delay")
                yield {"type": "error", "message": api.tr("status_user_cancelled")}
                api.abort_streams["default"] = False
                return

        yield {"type": "status", "message": api.tr("status_request_sent", provider=provider_label)}

        try:
            response = api.ai_client.models.generate_content(
                model=api.get_active_model(),
                contents=contents,
                config=config,
            )
        except Exception as api_err:
            error_msg = str(api_err)
            if _is_rate_limit_error(error_msg):
                low = error_msg.lower()
                # Detect exhausted daily/project quota (limit: 0 or per-day quota type)
                is_quota_exhausted = (
                    "limit: 0" in low
                    or "free_tier_requests" in low
                    or "per_day" in low
                    or "insufficient_quota" in low
                )
                rate_limit_retries += 1
                logger.warning(f"Google: Rate limit hit at round {round_num+1} (retry {rate_limit_retries}): {error_msg[:200]}")
                if is_quota_exhausted or rate_limit_retries > MAX_RATE_LIMIT_RETRIES:
                    # Quota is daily-exhausted or we've retried too many times — stop now
                    err_text = api.tr("err_google_quota") if is_quota_exhausted else api.tr("err_loop_exhausted")
                    logger.error(f"Google: Stopping retries (quota_exhausted={is_quota_exhausted}, retries={rate_limit_retries})")
                    yield {"type": "error", "message": err_text}
                    return
                yield {"type": "status", "message": api.tr("status_rate_limit_waiting")}
                time.sleep(10)
                continue  # Retry this round
            # Non-rate-limit error
            user_msg = _humanize_google_error(error_msg)
            logger.error(f"Google API error: {error_msg}")
            yield {"type": "error", "message": user_msg}
            return

        yield {"type": "status", "message": api.tr("status_response_received", provider=provider_label)}

        # Extract token usage from response
        usage_meta = getattr(response, "usage_metadata", None)
        if usage_meta:
            total_input_tokens += getattr(usage_meta, "prompt_token_count", 0) or 0
            total_output_tokens += getattr(usage_meta, "candidates_token_count", 0) or 0

        function_calls = getattr(response, "function_calls", None) or []
        if not function_calls:
            break

        round_num += 1
        logger.info(f"Google: Round {round_num}: {len(function_calls)} tool(s)")

        # Attach the function call content emitted by the model
        try:
            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)
        except Exception:
            pass

        tool_response_parts: list[types.Part] = []
        write_tool_result = None  # Track write tool for auto-stop
        redundant_blocked = 0

        for fc in function_calls:
            name = getattr(fc, "name", None)
            args = getattr(fc, "args", None)
            if not name and getattr(fc, "function_call", None):
                name = getattr(fc.function_call, "name", None)
                args = getattr(fc.function_call, "args", None)

            name = (name or "").strip()
            if not name:
                continue

            tool_args = dict(args) if isinstance(args, dict) else (dict(args) if args else {})

            # Redundancy detection: skip read-only tools already called with same args
            sig = f"{name}:{json.dumps(tool_args, sort_keys=True, default=str)}"
            if name in READ_ONLY_TOOLS and sig in tool_cache:
                logger.warning(f"Google: Reusing cached tool result: {name}")
                result = tool_cache[sig]
                redundant_blocked += 1
            else:
                yield {"type": "status", "message": api.tr("status_executing_tool", provider=provider_label, tool=name)}
                yield {"type": "tool", "name": name, "description": tools.get_tool_description(name)}

                result = _safe_execute_tool(name, tool_args)

                # Cache read-only tool results
                if name in READ_ONLY_TOOLS:
                    tool_cache[sig] = result

            # Tool result truncation (aligned with OpenAI provider)
            max_len = 20000 if name in READ_TOOLS_LARGE else 8000
            if len(result) > max_len:
                result = result[:max_len] + '\n... [TRUNCATED - ' + str(len(result)) + ' chars total]'

            # Track write tool result for auto-stop
            if name in WRITE_TOOLS:
                try:
                    parsed_result = json.loads(result)
                    if parsed_result.get("status") == "success" or parsed_result.get("url"):
                        write_tool_result = (name, parsed_result)
                except Exception:
                    pass

            try:
                parsed = json.loads(result)
            except Exception:
                parsed = result

            tool_response_parts.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": parsed},
                )
            )

        if tool_response_parts:
            contents.append(types.Content(role="tool", parts=tool_response_parts))

        # If ALL tools were cached/redundant, force stop to avoid infinite loops
        if redundant_blocked == len(function_calls):
            logger.info("Google: All tool calls were redundant — forcing final response")
            contents.append({"role": "user", "parts": [{"text": "You already have all the data. Respond to the user now. Do not call any more tools."}]})
            continue

        # AUTO-STOP: If a write tool succeeded, format response directly
        if write_tool_result:
            fn_name, result_data = write_tool_result
            # Skip auto-stop for draft HTML dashboards (both draft_started and draft_appended)
            if fn_name == "create_html_dashboard" and result_data.get("status") in ("draft_started", "draft_appended"):
                logger.info(f"Google: Draft dashboard {result_data.get('status')}, continuing...")
            # Skip auto-stop for empty dashboards (0 views)
            elif fn_name == "create_dashboard" and result_data.get("views_count", 1) == 0:
                logger.info("Google: Auto-stop skipped: create_dashboard with 0 views, letting model continue")
            else:
                logger.info(f"Google: Auto-stop after write tool '{fn_name}'")
                final_text = api._format_write_tool_response(fn_name, result_data)
                messages.append({"role": "assistant", "content": final_text})
                yield {"type": "clear"}
                for i in range(0, len(final_text), 4):
                    yield {"type": "token", "content": final_text[i:i+4]}
                yield {"type": "done", "full_text": final_text, "usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "model": api.get_active_model(),
                    "provider": "google",
                }}
                return

    if round_num >= MAX_ROUNDS:
        logger.warning(f"Google: Reached max rounds ({MAX_ROUNDS})")

    # Extract final text safely — Gemini SDK raises ValueError on .text
    # when response is blocked by safety filters or has no text parts
    final_text = ""
    if response is not None:
        try:
            final_text = response.text or ""
        except (ValueError, AttributeError) as e:
            logger.warning(f"Google: Could not extract response text: {e}")
            # Try to extract from candidates directly
            try:
                for candidate in (response.candidates or []):
                    for part in (candidate.content.parts or []):
                        if hasattr(part, "text") and part.text:
                            final_text += part.text
            except Exception:
                pass

    if not final_text:
        # Check if response was blocked by safety filters
        try:
            block_reason = None
            if response and hasattr(response, "prompt_feedback"):
                block_reason = getattr(response.prompt_feedback, "block_reason", None)
            if block_reason:
                logger.warning(f"Google: Response blocked by safety filters: {block_reason}")
                final_text = api.tr("err_response_blocked", provider="Google")
            else:
                logger.warning("Google: Empty response (no text, no tools) — showing fallback error")
                final_text = api.tr("err_loop_exhausted")
        except Exception:
            final_text = api.tr("err_loop_exhausted")

    # Stream text in 4-char chunks (smooth output, aligned with other providers)
    messages.append({"role": "assistant", "content": final_text})
    yield {"type": "clear"}
    if final_text:
        for i in range(0, len(final_text), 4):
            yield {"type": "token", "content": final_text[i:i+4]}
    yield {"type": "done", "full_text": final_text, "usage": {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "model": api.get_active_model(),
        "provider": "google",
    }}
