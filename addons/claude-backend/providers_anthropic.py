"""Anthropic Claude streaming provider for Home Assistant AI assistant."""

import json
import time
import logging

import api
import tools
import intent

logger = logging.getLogger(__name__)


def _is_rate_limit_error(error_msg: str) -> bool:
    """Return True if error message indicates rate limiting."""
    msg = (error_msg or "").lower()
    return (
        "429" in msg
        or "too many requests" in msg
        or "rate limit" in msg
        or "ratelimit" in msg
    )


def _humanize_anthropic_error(error_msg: str) -> str:
    """Return a user-friendly message for common Anthropic errors."""
    msg = error_msg or ""
    low = msg.lower()

    # API usage limits reached
    if "usage limits" in low or "specified api usage limits" in low:
        return {
            "en": "Anthropic: monthly API limit reached (next reset: March 1st). Switch to another provider or wait for the reset.",
            "it": "Anthropic: limite API mensile raggiunto (prossimo reset: 1 marzo). Cambia provider o aspetta il reset.",
            "es": "Anthropic: límite de API mensual alcanzado (próximo reset: 1 de marzo). Cambia de proveedor o espera el reset.",
            "fr": "Anthropic: limite d'API mensuelle atteinte (prochain reset: 1er mars). Changez de fournisseur ou attendez le reset.",
        }.get(api.LANGUAGE, "Anthropic: monthly API limit reached. Switch to another provider or wait for the reset on March 1st.")

    # Low credit / billing
    if "credit balance is too low" in low or "plans & billing" in low or "purchase credits" in low:
        return {
            "en": "Anthropic: insufficient credits. Open Plans & Billing to add credits, or switch provider.",
            "it": "Anthropic: credito insufficiente. Vai su Plans & Billing per acquistare crediti, oppure cambia provider.",
            "es": "Anthropic: crédito insuficiente. Ve a Plans & Billing para añadir créditos o cambia de proveedor.",
            "fr": "Anthropic: crédit insuffisant. Ouvrez Plans & Billing pour ajouter du crédit, ou changez de fournisseur.",
        }.get(api.LANGUAGE, "Anthropic: insufficient credits. Open Plans & Billing to add credits, or switch provider.")

    # Invalid/expired key
    if "authentication" in low or "invalid api key" in low or "x-api-key" in low or "unauthorized" in low:
        return {
            "en": "Anthropic: API key invalid or missing. Check your Anthropic API key in the add-on settings.",
            "it": "Anthropic: API key non valida o mancante. Controlla la chiave Anthropic nelle impostazioni dell’add-on.",
            "es": "Anthropic: API key inválida o ausente. Revisa la clave de Anthropic en la configuración del add-on.",
            "fr": "Anthropic: clé API invalide ou manquante. Vérifiez la clé Anthropic dans les paramètres de l’add-on.",
        }.get(api.LANGUAGE, "Anthropic: API key invalid or missing. Check your Anthropic API key in the add-on settings.")

    # Fallback: keep it short
    return {
        "en": "Anthropic error. Please retry or switch provider.",
        "it": "Errore Anthropic. Riprova oppure cambia provider.",
        "es": "Error de Anthropic. Reintenta o cambia de proveedor.",
        "fr": "Erreur Anthropic. Réessayez ou changez de fournisseur.",
    }.get(api.LANGUAGE, "Anthropic error. Please retry or switch provider.")


def stream_chat_anthropic(messages, intent_info=None):
    """Stream chat for Anthropic with real token streaming and tool event emission.
    Uses intent_info to select focused tools and prompt when available."""
    import anthropic

    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools") is not None:
        focused_prompt = intent.get_prompt_for_intent(intent_info)
        focused_tools = intent.get_tools_for_intent(intent_info, "anthropic")
        logger.info(f"Anthropic focused mode: {intent_info['intent']} ({len(focused_tools)} tools)")
    else:
        focused_prompt = tools.get_system_prompt()
        focused_tools = tools.get_anthropic_tools()

    # Log available tools for debugging
    tool_names = [t.get("name", "unknown") for t in focused_tools]
    logger.info(f"Anthropic tools available ({len(focused_tools)}): {', '.join(tool_names)}")

    full_text = ""
    max_rounds = (intent_info or {}).get("max_rounds") or 5
    tools_called_this_session = set()  # Track tools already called to detect redundancy
    total_input_tokens = 0
    total_output_tokens = 0
    last_read_content: dict = {}  # filename -> content (for proposal-phase diff injection)

    for round_num in range(max_rounds):
        # Check abort flag
        if api.abort_streams.get("default"):
            logger.info("Stream aborted by user")
            yield {"type": "error", "message": api.tr("status_user_cancelled")}
            api.abort_streams["default"] = False
            break
        # Rate-limit prevention: delay between API calls (not on first round)
        if round_num > 0:
            delay = min(3 + round_num, 6)  # 4s, 5s, 6s, 6s...
            logger.info(f"Rate-limit prevention: waiting {delay}s before round {round_num+1}")
            yield {"type": "status", "message": api.tr("status_rate_limit_wait_seconds", provider="Anthropic", seconds=delay)}
            time.sleep(delay)
            if api.abort_streams.get("default"):
                logger.info("Stream aborted by user during delay")
                yield {"type": "error", "message": api.tr("status_user_cancelled")}
                api.abort_streams["default"] = False
                break

        content_parts = []
        tool_uses = []
        current_tool_id = None
        current_tool_name = None
        current_tool_input_json = ""

        try:
            # Only pass tools if we have some (empty list = no tools for chat intent)
            call_kwargs = {
                "model": api.get_active_model(),
                "max_tokens": 8192,
                "system": focused_prompt,
                "messages": messages,
            }
            if focused_tools:
                call_kwargs["tools"] = focused_tools

            yield {"type": "status", "message": api.tr("status_request_sent", provider="Anthropic")}

            sent_streaming_status = False
            last_progress = time.monotonic()

            with api.ai_client.messages.stream(**call_kwargs) as stream:
                yield {"type": "status", "message": api.tr("status_response_received", provider="Anthropic")}
                for event in stream:
                    if not sent_streaming_status:
                        sent_streaming_status = True
                        yield {"type": "status", "message": api.tr("status_generating", provider="Anthropic")}
                    else:
                        now = time.monotonic()
                        if (now - last_progress) > 8:
                            last_progress = now
                            yield {"type": "status", "message": api.tr("status_still_working", provider="Anthropic")}
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_id = event.content_block.id
                            current_tool_name = event.content_block.name
                            current_tool_input_json = ""
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            content_parts.append(event.delta.text)
                        elif event.delta.type == "input_json_delta":
                            current_tool_input_json += event.delta.partial_json
                    elif event.type == "content_block_stop":
                        if current_tool_name:
                            try:
                                tool_input = json.loads(current_tool_input_json) if current_tool_input_json else {}
                            except json.JSONDecodeError:
                                tool_input = {}
                            tool_uses.append({
                                "id": current_tool_id,
                                "name": current_tool_name,
                                "input": tool_input
                            })
                            current_tool_name = None
                            current_tool_id = None
                            current_tool_input_json = ""

                final_message = stream.get_final_message()
                # Accumulate token usage across rounds
                if hasattr(final_message, 'usage') and final_message.usage:
                    total_input_tokens += getattr(final_message.usage, 'input_tokens', 0) or 0
                    total_output_tokens += getattr(final_message.usage, 'output_tokens', 0) or 0
        except Exception as api_err:
            error_msg = str(api_err)
            if _is_rate_limit_error(error_msg):
                logger.warning(f"Rate limit hit at round {round_num+1}: {error_msg}")
                yield {"type": "status", "message": api.tr("status_rate_limit_wait", provider="Anthropic")}
                time.sleep(10)  # Wait and retry this round
                continue

            # For common billing/auth issues, show a clean message instead of raw SDK payload
            user_msg = _humanize_anthropic_error(error_msg)
            logger.error(f"Anthropic API error: {error_msg}")
            yield {"type": "error", "message": user_msg}
            break

        accumulated_text = "".join(content_parts)

        if not tool_uses:
            # No tools - this is the final response. Stream the text now.
            full_text = accumulated_text
            logger.warning(f"Anthropic: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'")
            logger.info(f"Anthropic: This means the AI decided not to use any of the {len(focused_tools)} available tools")
            # For config_edit: inject diff view for display; keep full_text (with yaml) for message context
            display_text = full_text
            if last_read_content and (intent_info or {}).get("intent") == "config_edit":
                display_text = api._inject_proposal_diff(full_text, last_read_content)
                if display_text != full_text:
                    logger.info("Anthropic: injected proposal diff into display text")
            # Yield a clear signal to reset any previous tool badges
            yield {"type": "clear"}
            for i in range(0, len(display_text), 4):
                chunk = display_text[i:i+4]
                yield {"type": "token", "content": chunk}
            break

        # Tools found - DON'T stream intermediate text, just show tool badges
        logger.info(f"Round {round_num+1}: {len(tool_uses)} tool(s), skipping intermediate text")
        yield {"type": "status", "message": api.tr("status_actions_received")}
        # For Anthropic, use the full content list which includes tool_use blocks
        assistant_content = final_message.content
        # REQUIRED: Anthropic needs the assistant message with tool_use blocks
        # before the user message with tool_result blocks
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        redundant_blocked = 0
        for tool in tool_uses:
            tool_key = tool['name']
            # Block redundant calls: if a read-only tool was already called, skip it
            redundant_read_tools = {"get_automations", "get_scripts", "get_dashboards",
                                    "get_dashboard_config", "read_config_file",
                                    "list_config_files", "get_frontend_resources",
                                    "search_entities", "get_entity_state"}
            if tool_key in redundant_read_tools and tool_key in tools_called_this_session:
                logger.warning(f"Blocked redundant tool call: {tool_key} (already called this session)")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool["id"],
                    "content": json.dumps({"note": f"Skipped: {tool_key} already called. Use the data you already have. Respond to the user NOW."})
                })
                redundant_blocked += 1
                continue

            logger.info(f"Anthropic: Executing tool '{tool['name']}' with input: {tool['input']}")
            yield {"type": "status", "message": api.tr("status_executing_tool", provider="Anthropic", tool=tool["name"]) }
            
            # Build a more detailed tool description with parameters
            tool_desc = tools.get_tool_description(tool["name"])
            tool_input = tool.get("input", {})
            if tool_input:
                if isinstance(tool_input, dict):
                    if "filename" in tool_input:
                        tool_desc += f": {tool_input['filename']}"
                    elif "entity_id" in tool_input:
                        tool_desc += f": {tool_input['entity_id']}"
                    elif "automation_id" in tool_input:
                        tool_desc += f": {tool_input['automation_id']}"
            
            yield {"type": "tool", "name": tool["name"], "description": tool_desc}
            try:
                result = tools.execute_tool(tool["name"], tool["input"])
            except Exception as e:
                logger.exception(f"Anthropic: Tool execution failed: {tool['name']}: {e}")
                result = json.dumps({"error": f"Tool '{tool['name']}' failed: {str(e)}"}, ensure_ascii=False)
            logger.info(f"Anthropic: Tool '{tool['name']}' returned {len(result)} chars: {result[:300]}...")
            tools_called_this_session.add(tool_key)
            # Cache read_config_file content for proposal-phase diff
            if tool["name"] == "read_config_file":
                try:
                    rdata = json.loads(result)
                    if rdata.get("content"):
                        last_read_content[rdata.get("filename", "__last__")] = rdata["content"]
                except Exception:
                    pass
            # Truncate large tool results to prevent token overflow
            _read_tools_large = {"read_config_file", "get_entity_details", "get_entity_history"}
            max_len = 20000 if tool["name"] in _read_tools_large else 8000
            if len(result) > max_len:
                result = result[:max_len] + '\n... [TRUNCATED - ' + str(len(result)) + ' chars total]'
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool["id"],
                "content": result
            })

        # If ALL tools were blocked as redundant, force stop
        if redundant_blocked == len(tool_uses):
            logger.info("All tool calls were redundant - forcing final response")
            if api.AI_PROVIDER in ("openai", "github"):
                for tr in tool_results:
                    messages.append({"role": "tool", "tool_call_id": tr["tool_use_id"], "content": tr["content"]})
            else:
                messages.append({"role": "user", "content": tool_results})
            messages.append({"role": "user", "content": [{"type": "text", "text": "You already have all the data needed. Respond to the user now with the results. Do not call any more tools."}]})
            continue

        # AUTO-STOP: If a write tool succeeded, format response directly — no more API calls needed
        WRITE_TOOLS = {"update_automation", "update_script", "update_dashboard_card",
                   "create_automation", "create_script", "create_dashboard", "update_dashboard",
                   "create_html_dashboard", "write_config_file"}
        auto_stop = False
        for tool in tool_uses:
            if tool["name"] in WRITE_TOOLS:
                for tr in tool_results:
                    if tr.get("tool_use_id") == tool["id"]:
                        try:
                            rdata = json.loads(tr["content"])
                            if rdata.get("status") == "success" or rdata.get("url"):
                                # Skip auto-stop for draft HTML dashboards
                                if tool["name"] == "create_html_dashboard" and rdata.get("status") in ("draft_started", "draft_appended"):
                                    logger.info(f"Auto-stop skipped: draft dashboard {rdata.get('status')}")
                                # Skip auto-stop for empty dashboards (0 views) - model needs to continue
                                elif tool["name"] == "create_dashboard" and rdata.get("views_count", 1) == 0:
                                    logger.info("Auto-stop skipped: create_dashboard with 0 views, letting model continue")
                                else:
                                    auto_stop = True
                                    full_text = api._format_write_tool_response(tool["name"], rdata)
                        except (json.JSONDecodeError, KeyError):
                            pass
                        break
            if auto_stop:
                break

        if auto_stop:
            logger.info(f"Auto-stop: write tool succeeded, skipping further API calls")
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                yield {"type": "token", "content": full_text[i:i+4]}
            break

        if api.AI_PROVIDER in ("openai", "github"):
            for tr in tool_results:
                messages.append({"role": "tool", "tool_call_id": tr["tool_use_id"], "content": tr["content"]})
        else:
            messages.append({"role": "user", "content": tool_results})
        # Loop back for next round

    messages.append({"role": "assistant", "content": full_text})
    yield {"type": "done", "full_text": full_text, "usage": {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "model": api.get_active_model(),
        "provider": "anthropic",
    }}
