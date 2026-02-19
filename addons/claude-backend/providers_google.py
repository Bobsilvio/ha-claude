"""Google Gemini streaming provider for Home Assistant AI assistant."""

import json
import time
import logging

import api
import tools

logger = logging.getLogger(__name__)


def stream_chat_google(messages, intent_info: dict | None = None):
    """Stream chat for Google Gemini with tool events. Falls back to word-by-word for text.
    Supports intent_info for focused mode, WRITE_TOOLS auto-stop, max rounds, and abort."""
    from google.genai import types

    provider_label = "Google"
    MAX_ROUNDS = 10

    # WRITE_TOOLS auto-stop: after these tools succeed, format response directly
    WRITE_TOOLS = {"update_automation", "update_script", "update_dashboard_card",
                   "create_automation", "create_script", "create_dashboard", "update_dashboard",
                   "create_html_dashboard"}

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
    while round_num < MAX_ROUNDS:
        # Check abort flag
        if api.abort_streams.get("default"):
            logger.info("Google: Stream aborted by user")
            yield {"type": "error", "message": api.tr("status_user_cancelled")}
            api.abort_streams["default"] = False
            return

        yield {"type": "status", "message": api.tr("status_request_sent", provider=provider_label)}
        response = api.ai_client.models.generate_content(
            model=api.get_active_model(),
            contents=contents,
            config=config,
        )
        yield {"type": "status", "message": api.tr("status_response_received", provider=provider_label)}

        function_calls = getattr(response, "function_calls", None) or []
        if not function_calls:
            break

        round_num += 1
        logger.info(f"Google: Round {round_num}: {len(function_calls)} tool(s)")

        # Attach the function call content emitted by the model.
        try:
            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)
        except Exception:
            pass

        tool_response_parts: list[types.Part] = []
        write_tool_result = None  # Track write tool for auto-stop

        for fc in function_calls:
            name = getattr(fc, "name", None)
            args = getattr(fc, "args", None)
            if not name and getattr(fc, "function_call", None):
                name = getattr(fc.function_call, "name", None)
                args = getattr(fc.function_call, "args", None)

            name = (name or "").strip()
            if not name:
                continue

            yield {"type": "status", "message": api.tr("status_executing_tool", provider=provider_label, tool=name)}
            yield {"type": "tool", "name": name, "description": tools.get_tool_description(name)}

            tool_args = dict(args) if isinstance(args, dict) else (dict(args) if args else {})
            result = tools.execute_tool(name, tool_args)

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

        # AUTO-STOP: If a write tool succeeded, format response directly
        if write_tool_result:
            fn_name, result_data = write_tool_result
            # Skip auto-stop for draft HTML dashboards
            if fn_name == "create_html_dashboard" and result_data.get("status") == "draft_started":
                logger.info(f"Google: Draft dashboard started, continuing...")
            else:
                logger.info(f"Google: Auto-stop after write tool '{fn_name}'")
                final_text = api._format_write_tool_response(fn_name, result_data)
                messages.append({"role": "assistant", "content": final_text})
                yield {"type": "clear"}
                words = final_text.split(' ')
                for i, word in enumerate(words):
                    yield {"type": "token", "content": word + (' ' if i < len(words) - 1 else '')}
                yield {"type": "done", "full_text": final_text}
                return

        # Rate-limit prevention for Google
        time.sleep(1)

    if round_num >= MAX_ROUNDS:
        logger.warning(f"Google: Reached max rounds ({MAX_ROUNDS})")

    final_text = (getattr(response, "text", None) or "") if response is not None else ""

    # Stream text word by word
    messages.append({"role": "assistant", "content": final_text})
    yield {"type": "clear"}
    words = final_text.split(' ')
    for i, word in enumerate(words):
        yield {"type": "token", "content": word + (' ' if i < len(words) - 1 else '')}
    yield {"type": "done", "full_text": final_text}
