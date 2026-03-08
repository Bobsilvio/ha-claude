#!/usr/bin/env python3
"""Quick smoke test for tool_registry.py — run standalone."""
import json
import os
import sys

# Allow running from tests/ directory by adding parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tool_registry import (
    ToolDefinition, ToolCategory, ToolRegistry,
    FileAccessPolicy, TierPolicy, IntentPolicy,
    AnthropicAdapter, OpenAIAdapter, GeminiAdapter,
    ReadOnlyHook, DuplicateCallHook, EntityValidationHook, LoggingHook,
    ToolCallContext, get_adapter,
)


def fake_execute(args):
    return '{"result": "ok"}'


def test_policies():
    t1 = ToolDefinition(
        name="get_entities", description="Get HA entity states",
        parameters={"type": "object", "properties": {"domain": {"type": "string"}}, "required": ["domain"]},
        execute=fake_execute, category=ToolCategory.QUERY, read_only=True,
        tier_compact=True, tier_extended=True, user_description="Recupero entita",
    )
    t2 = ToolDefinition(
        name="call_service", description="Call an HA service",
        parameters={"type": "object", "properties": {"domain": {"type": "string"}, "service": {"type": "string"}}, "required": ["domain", "service"]},
        execute=fake_execute, category=ToolCategory.CONTROL, read_only=False,
        tier_compact=True, tier_extended=True,
    )
    t3 = ToolDefinition(
        name="read_config_file", description="Read config file",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        execute=fake_execute, category=ToolCategory.CONFIG, read_only=True,
        tier_compact=False, tier_extended=True,
    )

    reg = ToolRegistry()
    reg.add_policy(FileAccessPolicy())
    reg.add_policy(TierPolicy())
    reg.add_policy(IntentPolicy())
    reg.register_many([t1, t2, t3])

    # Full tier, all intents, file_access=True -> 3 tools
    ctx = {"tier": "full", "enable_file_access": True}
    assert len(reg.get_tools(ctx)) == 3, f"Full tier: expected 3, got {len(reg.get_tools(ctx))}"

    # Block config when file_access=False
    ctx = {"tier": "full", "enable_file_access": False}
    assert len(reg.get_tools(ctx)) == 2, f"No file access: expected 2, got {len(reg.get_tools(ctx))}"

    # Compact tier -> only compact tools (t1, t2)
    ctx = {"tier": "compact", "enable_file_access": True}
    got = reg.get_tools(ctx)
    assert len(got) == 2, f"Compact: expected 2, got {len(got)}"

    # Intent filter -> subset
    ctx = {"tier": "full", "enable_file_access": True, "intent_tools": ["get_entities"]}
    assert len(reg.get_tools(ctx)) == 1

    # Empty intent -> no tools
    ctx = {"tier": "full", "enable_file_access": True, "intent_tools": []}
    assert len(reg.get_tools(ctx)) == 0

    print("  [OK] Policy filtering")
    return reg


def test_adapters(reg):
    ctx = {"tier": "full", "enable_file_access": True}

    # Anthropic format
    anthr = reg.format_for_provider("anthropic", ctx)
    assert anthr[0]["name"] == "get_entities"
    assert "input_schema" in anthr[0]

    # OpenAI format
    oai = reg.format_for_provider("openai", ctx)
    assert oai[0]["type"] == "function"
    assert "function" in oai[0]
    assert oai[0]["function"]["name"] == "get_entities"

    # OpenAI-compatible providers share adapter
    for p in ("github", "nvidia", "groq", "mistral", "deepseek", "openrouter"):
        result = reg.format_for_provider(p, ctx)
        assert result[0]["type"] == "function", f"{p} adapter failed"

    print("  [OK] Provider adapters")


def test_hooks(reg):
    reg.add_before_hook(ReadOnlyHook())
    reg.add_before_hook(EntityValidationHook())
    reg.add_before_hook(DuplicateCallHook())
    reg.add_after_hook(LoggingHook())

    # Normal execution
    result = reg.execute("get_entities", {"domain": "light"})
    assert "result" in result, f"Normal exec failed: {result}"

    # Entity validation hook - invalid entity_id
    ctx = ToolCallContext(tool_name="call_service", arguments={"entity_id": "badformat"})
    result = reg.execute("call_service", {"entity_id": "badformat"}, context=ctx)
    parsed = json.loads(result)
    assert "error" in parsed, f"EntityValidation should block: {result}"

    # Read-only hook
    ctx = ToolCallContext(
        tool_name="call_service",
        arguments={"domain": "light", "service": "turn_on"},
        read_only=True,
    )
    result = reg.execute("call_service", {"domain": "light", "service": "turn_on"}, context=ctx)
    parsed = json.loads(result)
    assert parsed["status"] == "read_only", f"ReadOnly should block: {result}"

    print("  [OK] Hooks (ReadOnly, EntityValidation, Duplicate, Logging)")


def test_stats(reg):
    stats = reg.get_stats()
    assert stats["registered_tools"] == 3
    assert stats["call_counts"].get("get_entities", 0) >= 1
    assert "query" in stats["categories"]
    print(f"  [OK] Stats: {stats['categories']}")


def test_from_legacy():
    """Test bridge from legacy HA_TOOLS_DESCRIPTION format."""
    legacy_tools = [
        {"name": "get_entities", "description": "Get entities", "parameters": {"type": "object", "properties": {}}},
        {"name": "call_service", "description": "Call service", "parameters": {"type": "object", "properties": {}}},
        {"name": "create_automation", "description": "Create auto", "parameters": {"type": "object", "properties": {}}},
    ]

    def legacy_execute(name, args):
        return json.dumps({"tool": name, "status": "ok"})

    reg = ToolRegistry.from_legacy_tools(
        tool_descriptions=legacy_tools,
        execute_fn=legacy_execute,
        write_tools={"call_service", "create_automation"},
        compact_tools={"get_entities", "call_service"},
        extended_tools={"get_entities", "call_service", "create_automation"},
    )

    assert reg.tool_count == 3

    # Test inferred categories
    t = reg.get_tool("get_entities")
    assert t.category == ToolCategory.QUERY
    assert t.read_only is True
    assert t.tier_compact is True

    t = reg.get_tool("call_service")
    assert t.category == ToolCategory.CONTROL
    assert t.read_only is False

    t = reg.get_tool("create_automation")
    assert t.category == ToolCategory.AUTOMATION

    # Test execution through wrapper
    result = reg.execute("get_entities", {})
    parsed = json.loads(result)
    assert parsed["tool"] == "get_entities"

    print("  [OK] Legacy bridge (from_legacy_tools)")


def test_gemini_sanitize():
    """Test Gemini adapter strips blocked keywords."""
    adapter = GeminiAdapter()
    schema = {
        "type": "object",
        "properties": {
            "temp": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
                "format": "float",
                "description": "Temperature",
            }
        },
        "required": ["temp"],
    }
    tool = ToolDefinition(
        name="set_temp", description="Set temperature",
        parameters=schema, execute=fake_execute,
    )
    formatted = adapter.format_tool(tool)
    params = formatted["parameters_json_schema"]
    temp_prop = params["properties"]["temp"]

    # Blocked keys should be stripped
    assert "minimum" not in temp_prop, "minimum should be stripped for Gemini"
    assert "maximum" not in temp_prop, "maximum should be stripped for Gemini"
    assert "format" not in temp_prop, "format should be stripped for Gemini"
    # Valid keys should remain
    assert temp_prop["type"] == "number"
    assert temp_prop["description"] == "Temperature"

    print("  [OK] Gemini schema sanitization")


if __name__ == "__main__":
    print("Tool Registry Tests:")
    reg = test_policies()
    test_adapters(reg)
    test_hooks(reg)
    test_stats(reg)
    test_from_legacy()
    test_gemini_sanitize()
    print("\nAll tests passed.")
    sys.exit(0)
