"""Anthropic Claude streaming provider for Home Assistant AI assistant."""

import json
import time
import logging

import api
import tools
import intent

logger = logging.getLogger(__name__)


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

    for round_num in range(max_rounds):
        # Check abort flag
        if api.abort_streams.get("default"):
            logger.info("Stream aborted by user")
            yield {"type": "error", "message": "Interrotto dall'utente."}
            api.abort_streams["default"] = False
            break
        # Rate-limit prevention: delay between API calls (not on first round)
        if round_num > 0:
            delay = min(3 + round_num, 6)  # 4s, 5s, 6s, 6s...
            logger.info(f"Rate-limit prevention: waiting {delay}s before round {round_num+1}")
            yield {"type": "status", "message": f"Elaboro la risposta... (step {round_num+1})"}
            time.sleep(delay)
            if api.abort_streams.get("default"):
                logger.info("Stream aborted by user during delay")
                yield {"type": "error", "message": "Interrotto dall'utente."}
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

            with api.ai_client.messages.stream(**call_kwargs) as stream:
                for event in stream:
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
        except Exception as api_err:
            error_msg = str(api_err)
            if "429" in error_msg or "rate" in error_msg.lower():
                logger.warning(f"Rate limit hit at round {round_num+1}: {error_msg}")
                yield {"type": "status", "message": "Rate limit raggiunto, attendo..."}
                time.sleep(10)  # Wait and retry this round
                continue
            else:
                raise

        accumulated_text = "".join(content_parts)

        if not tool_uses:
            # No tools - this is the final response. Stream the text now.
            full_text = accumulated_text
            logger.warning(f"Anthropic: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'")
            logger.info(f"Anthropic: This means the AI decided not to use any of the {len(focused_tools)} available tools")
            # Save assistant message to conversation
            messages.append({"role": "assistant", "content": full_text})
            # Yield a clear signal to reset any previous tool badges
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                chunk = full_text[i:i+4]
                yield {"type": "token", "content": chunk}
            break

        # Tools found - DON'T stream intermediate text, just show tool badges
        logger.info(f"Round {round_num+1}: {len(tool_uses)} tool(s), skipping intermediate text")
        # For Anthropic, use the full content list which includes tool_use blocks
        assistant_content = final_message.content
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
            yield {"type": "tool", "name": tool["name"], "description": tools.get_tool_description(tool["name"])}
            result = tools.execute_tool(tool["name"], tool["input"])
            logger.info(f"Anthropic: Tool '{tool['name']}' returned {len(result)} chars: {result[:300]}...")
            tools_called_this_session.add(tool_key)
            # Truncate large tool results to prevent token overflow
            if len(result) > 8000:
                result = result[:8000] + '\n... [TRUNCATED to save tokens - ' + str(len(result)) + ' chars total]'
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
                       "create_automation", "create_script", "create_dashboard", "update_dashboard"}
        auto_stop = False
        for tool in tool_uses:
            if tool["name"] in WRITE_TOOLS:
                for tr in tool_results:
                    if tr.get("tool_use_id") == tool["id"]:
                        try:
                            rdata = json.loads(tr["content"])
                            if rdata.get("status") == "success":
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
    yield {"type": "done", "full_text": full_text}
