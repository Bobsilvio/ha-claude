"""tool_simulator.py — Universal tool-call simulator for providers without native tool support.

Providers like claude_web, chatgpt_web, github_copilot, openai_codex cannot receive
tool schemas or return structured tool_calls.  Instead we instruct them (via a system
prompt) to embed tool invocations in the response as an XML block:

    <tool_call>
    {"name": "create_automation", "arguments": {...}}
    </tool_call>

This module:
  1. Provides the universal system-prompt fragment to inject into any no-tool provider.
  2. Parses the accumulated text response and extracts those blocks.
  3. Returns a list of tool_call dicts in the same format used by the native tool loop
     in api.py — so zero changes are needed in the main loop logic.

The `create_html_dashboard` intent is intentionally excluded: the model must produce
free-form HTML, which is beautiful and unique for each request.  We never want to
standardise that into a rigid tool-call structure.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intents that use the simulator (write operations requiring confirmation)
# ---------------------------------------------------------------------------
SIMULATED_INTENTS = {
    "create_automation",
    "modify_automation",
    "create_script",
    "modify_script",
    "helpers",
    "control_device",
    "delete",
    "notifications",
    "areas",
    "config_edit",
}

# Intents that must remain free-form (no simulator)
FREE_FORM_INTENTS = {
    "create_html_dashboard",  # free creative HTML — keep as-is
}

# ---------------------------------------------------------------------------
# Regex to find <tool_call> blocks
# ---------------------------------------------------------------------------
_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*([\s\S]*?)\s*</tool_call>",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Universal system-prompt fragment
# ---------------------------------------------------------------------------

_TOOL_CALL_INSTRUCTIONS = """\
You cannot call tools directly. Instead, embed tool invocations as structured XML \
blocks in your response:

<tool_call>
{"name": "<tool_name>", "arguments": {<json_arguments>}}
</tool_call>

The system parses these blocks automatically — NEVER explain the XML to the user.
Available tools and their argument schemas are listed in the TOOLS section below.

CRITICAL RULES — follow exactly:

READ-ONLY tools (get_*, search_*, list_*, get_automations, get_scripts, \
get_entities, search_entities):
  - Output ONLY the <tool_call> block. NO introductory text, NO explanation before it.
  - After receiving the tool result, answer the user using the data returned.

WRITE/DESTRUCTIVE tools (create_*, update_*, delete_*, manage_*, \
create_automation, update_automation, create_script, update_script):
  - First describe to the user what you plan to do and ask for confirmation \
(sì / yes / ok / confirm).
  - Only emit the <tool_call> block AFTER the user explicitly confirms.

OTHER rules:
- NEVER invent entity_ids — only use ids found in the CONTEXT or DATA sections.
- ALWAYS respond in the user's language.
- You MAY emit multiple <tool_call> blocks in one response if needed.
"""


def build_tools_schema_text(tool_schemas: List[Dict[str, Any]]) -> str:
    """Convert the list of tool dicts to a compact human-readable schema block.

    Handles both flat format  {"name":..., "description":..., "parameters":...}
    and OpenAI function format {"type":"function","function":{"name":...,...}}.
    """
    if not tool_schemas:
        return ""
    lines = ["TOOLS:"]
    for t in tool_schemas:
        # Support OpenAI format: {"type": "function", "function": {...}}
        if "function" in t and isinstance(t["function"], dict):
            fn = t["function"]
            name = fn.get("name", "")
            desc = fn.get("description", "")[:120]
            params = fn.get("parameters", {}).get("properties", {})
            required = fn.get("parameters", {}).get("required", [])
        else:
            # Flat format: {"name":..., "description":..., "parameters":...}
            name = t.get("name", "")
            desc = t.get("description", "")[:120]
            params = t.get("parameters", {}).get("properties", {})
            required = t.get("parameters", {}).get("required", [])
        if not name:
            continue
        param_parts = []
        for pname, pdef in params.items():
            ptype = pdef.get("type", "any")
            req = "*" if pname in required else "?"
            param_parts.append(f"{pname}{req}:{ptype}")
        sig = f"  {name}({', '.join(param_parts)})"
        lines.append(sig)
        lines.append(f"    # {desc}")
    return "\n".join(lines)


def get_simulator_system_prompt(tool_schemas: Optional[List[Dict[str, Any]]] = None) -> str:
    """Return the full system-prompt fragment for no-tool providers."""
    prompt = _TOOL_CALL_INSTRUCTIONS
    if tool_schemas:
        prompt += "\n\n" + build_tools_schema_text(tool_schemas)
    return prompt


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def extract_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Parse <tool_call> blocks from a model response.

    Returns a list of dicts compatible with the api.py tool loop:
        [{"id": "sim_0", "name": "create_automation", "arguments": "{...}"}]

    Returns an empty list if no blocks are found.
    """
    calls = []
    for i, match in enumerate(_TOOL_CALL_RE.finditer(text)):
        raw = match.group(1).strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            # Try to repair common model mistakes: trailing commas, single quotes
            try:
                repaired = _repair_json(raw)
                payload = json.loads(repaired)
            except Exception:
                logger.warning(f"ToolSimulator: could not parse tool_call block #{i}: {raw[:200]}")
                continue

        name = payload.get("name", "")
        arguments = payload.get("arguments", {})

        if not name:
            logger.warning(f"ToolSimulator: tool_call block #{i} missing 'name' field")
            continue

        # Normalise arguments to JSON string (api.py expects string, then json.loads it)
        if isinstance(arguments, dict):
            arguments_str = json.dumps(arguments, ensure_ascii=False)
        elif isinstance(arguments, str):
            arguments_str = arguments
        else:
            arguments_str = json.dumps(arguments, ensure_ascii=False)

        calls.append({
            "id": f"sim_{i}",
            "name": name,
            "arguments": arguments_str,
        })
        logger.info(f"ToolSimulator: found tool_call '{name}' (block #{i})")

    return calls


def clean_response_text(text: str) -> str:
    """Remove <tool_call> blocks from the text before displaying to the user."""
    cleaned = _TOOL_CALL_RE.sub("", text)
    # Collapse multiple blank lines left by removal
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Message normaliser — flatten tool-call history for no-native-tool providers
# ---------------------------------------------------------------------------

def flatten_tool_messages(
    messages: List[Dict[str, Any]],
    max_result_chars: int = 3000,
) -> List[Dict[str, Any]]:
    """Convert OpenAI tool-call history into plain user/assistant messages.

    Providers without native tool support (claude_web, chatgpt_web,
    github_copilot, openai_codex) don't understand role='tool' or
    the 'tool_calls' field on assistant messages.  This function:

    1. Strips 'tool_calls' from assistant messages (keeps visible text).
    2. Merges each role='tool' result into the preceding assistant message
       as a readable [TOOL RESULT: name] block.

    The returned list contains only role=system/user/assistant messages
    that every provider can handle.
    """
    out: List[Dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "")

        if role == "tool":
            # Merge into the previous assistant message as a readable block
            tool_name = m.get("name", "")
            content = m.get("content", "") or ""
            if len(content) > max_result_chars:
                content = content[:max_result_chars] + "\n... [truncated]"
            block = f"[TOOL RESULT: {tool_name}]\n{content}\n[/TOOL RESULT]"
            if out and out[-1].get("role") == "assistant":
                prev = dict(out[-1])
                prev_text = prev.get("content") or ""
                prev["content"] = (prev_text + "\n" + block).strip()
                out[-1] = prev
            else:
                # No preceding assistant turn — attach as a new assistant message
                out.append({"role": "assistant", "content": block})
            continue

        if role == "assistant":
            # Keep visible text; replace empty content with tool-call summary
            m2 = {k: v for k, v in m.items() if k != "tool_calls"}
            if not (m2.get("content") or "").strip():
                tcs = m.get("tool_calls", [])
                if tcs:
                    names = ", ".join(
                        tc.get("function", {}).get("name", tc.get("name", "?"))
                        for tc in tcs
                    )
                    m2["content"] = f"[Called tools: {names}]"
            out.append(m2)
            continue

        # system / user — pass through unchanged
        out.append(m)

    return out


# ---------------------------------------------------------------------------
# JSON repair helpers
# ---------------------------------------------------------------------------

def _repair_json(raw: str) -> str:
    """Best-effort repair of slightly malformed JSON from LLMs."""
    # Replace single quotes used as string delimiters
    # (only outside already-valid double-quoted strings — simple heuristic)
    repaired = raw
    # Trailing commas before } or ]
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    # Python-style True/False/None
    repaired = repaired.replace("True", "true").replace("False", "false").replace("None", "null")
    return repaired
