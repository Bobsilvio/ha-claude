from providers.google import GoogleProvider


def test_sanitize_removes_empty_enum_strings_recursively():
    schema = {
        "type": "object",
        "properties": {
            "disabled_by": {"type": "string", "enum": ["automation", ""]},
            "nested": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["a", "", "b"]}
                },
            },
        },
    }

    cleaned = GoogleProvider._sanitize_function_parameters_for_gemini(schema)

    assert cleaned["properties"]["disabled_by"]["enum"] == ["automation"]
    assert cleaned["properties"]["nested"]["properties"]["mode"]["enum"] == ["a", "b"]


def test_sanitize_does_not_mutate_original_schema():
    schema = {"type": "string", "enum": ["x", ""]}

    cleaned = GoogleProvider._sanitize_function_parameters_for_gemini(schema)

    assert schema["enum"] == ["x", ""]
    assert cleaned["enum"] == ["x"]
