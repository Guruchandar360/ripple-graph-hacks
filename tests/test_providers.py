import asyncio
import json
from dataclasses import replace

import httpx
from google.genai import types

from ripple.agent import declarations
from ripple.providers import OllamaAdapter, json_schema, ollama_messages


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


def test_explicit_json_protocol_preserves_model_selected_tool_and_arguments(monkeypatch):
    captured = {}

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, **kwargs):
            captured.update(kwargs["json"])
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={
                    "message": {
                        "content": json.dumps(
                            {"tool_calls": [{"name": "probe_service", "arguments": {"service": "ledger"}}]}
                        )
                    }
                },
            )

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    result = asyncio.run(
        OllamaAdapter("http://local", tool_mode="json").generate_content(
            model="test",
            contents=[],
            tool_catalog=declarations("graph"),
            config=types.GenerateContentConfig(
                system_instruction="test",
                tools=[
                    types.Tool(
                        function_declarations=[f for f in declarations("graph") if f.name == "probe_service"]
                    )
                ],
            ),
        )
    )
    call = result.candidates[0].content.parts[0].function_call
    assert call.name == "probe_service" and call.args == {"service": "ledger"}
    assert "tools" not in captured
    assert captured["format"]["required"] == ["tool_calls"]
    assert "retrieve_memory" in captured["messages"][0]["content"]
    assert "retrieve_memory" not in captured["messages"][-1]["content"]
    assert len(captured["format"]["properties"]["tool_calls"]["items"]["anyOf"]) == 1
