from dataclasses import replace

from google.genai import types

from ripple.agent import declarations
from ripple.providers import json_schema, ollama_messages


def test_explicit_local_provider_does_not_require_or_invent_a_cloud_key(settings):
    local = replace(settings, api_key="", provider="ollama", ollama_model="qwen3:1.7b")
    assert local.model_configured
    assert local.active_model == "qwen3:1.7b"
    assert not replace(local, provider="gemini").model_configured


def test_native_ollama_schema_preserves_action_values_and_required_fields():
    proposal = next(f for f in declarations("graph") if f.name == "propose_action")
    schema = json_schema(proposal.parameters.model_dump(mode="json", exclude_none=True))
    assert schema["type"] == "object"
    assert schema["properties"]["evidence_ids"]["type"] == "array"
    assert "rollback_deployment" in schema["properties"]["action"]["enum"]
    assert "evidence_ids" in schema["required"]


def test_tool_observations_are_forwarded_faithfully_without_becoming_user_instructions():
    contents = [
        types.Content(
            role="model", parts=[types.Part(function_call=types.FunctionCall(name="get_context", args={}))]
        ),
        types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name="get_context", response={"evidence_ids": ["real-source"]}
                )
            ],
        ),
    ]
    messages = ollama_messages("System policy", contents)
    assert messages[0] == {"role": "system", "content": "System policy"}
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "tool"
    assert messages[2]["tool_name"] == "get_context"
    assert "real-source" in messages[2]["content"]
