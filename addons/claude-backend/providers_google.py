"""Google Gemini streaming provider for Home Assistant AI assistant."""

import json
import time
import logging

import api
import tools

logger = logging.getLogger(__name__)


def stream_chat_google(messages):
    """Stream chat for Google Gemini with tool events. Falls back to word-by-word for text."""
    from google.generativeai.types import content_types

    model = api.ai_client.GenerativeModel(
        model_name=api.get_active_model(),
        system_instruction=tools.get_system_prompt(),
        tools=[tools.get_gemini_tools()]
    )

    gemini_history = []
    for m in messages[:-1]:
        role = "model" if m["role"] == "assistant" else "user"
        if isinstance(m.get("content"), str):
            gemini_history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=gemini_history)
    last_message = messages[-1]["content"] if messages else ""
    response = chat.send_message(last_message)

    while response.candidates[0].content.parts:
        has_function_call = False
        function_responses = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                has_function_call = True
                fn = part.function_call
                logger.info(f"Tool: {fn.name}")
                yield {"type": "tool", "name": fn.name}
                args = dict(fn.args) if fn.args else {}
                result = tools.execute_tool(fn.name, args)
                function_responses.append(
                    api.ai_client.protos.Part(function_response=api.ai_client.protos.FunctionResponse(
                        name=fn.name,
                        response={"result": json.loads(result)}
                    ))
                )

        if not has_function_call:
            break
        # Rate-limit prevention for Google
        time.sleep(1)
        response = chat.send_message(function_responses)

    final_text = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "text") and part.text:
            final_text += part.text

    # Stream text word by word
    messages.append({"role": "assistant", "content": final_text})
    words = final_text.split(' ')
    for i, word in enumerate(words):
        yield {"type": "token", "content": word + (' ' if i < len(words) - 1 else '')}
    yield {"type": "done", "full_text": final_text}
