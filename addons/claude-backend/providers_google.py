"""Google Gemini streaming provider for Home Assistant AI assistant."""

import json
import time
import logging

import api
import tools

logger = logging.getLogger(__name__)


def stream_chat_google(messages):
    """Stream chat for Google Gemini with tool events. Falls back to word-by-word for text."""
    from google.genai import types

    provider_label = "Google"

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

    tool = tools.get_gemini_tools()
    config = types.GenerateContentConfig(
        system_instruction=tools.get_system_prompt(),
        tools=[tool],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    response = None
    while True:
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

        # Attach the function call content emitted by the model.
        try:
            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)
        except Exception:
            pass

        tool_response_parts: list[types.Part] = []
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

        # Rate-limit prevention for Google
        time.sleep(1)

    final_text = (getattr(response, "text", None) or "") if response is not None else ""

    # Stream text word by word
    # L'aggiunta a messages viene fatta solo qui, non altrove
    messages.append({"role": "assistant", "content": final_text})
    yield {"type": "clear"}
    words = final_text.split(' ')
    for i, word in enumerate(words):
        yield {"type": "token", "content": word + (' ' if i < len(words) - 1 else '')}
    yield {"type": "done", "full_text": final_text}
