"""Optional Ollama native tools adapter. Selection is explicit, never an automatic fallback."""

import json
from types import SimpleNamespace

import httpx
from google.genai import types

from ripple.models import DomainError


def json_schema(schema):
    if isinstance(schema, list):
        return [json_schema(value) for value in schema]
    if not isinstance(schema, dict):
        return schema
    return {
        key: value.lower() if key == "type" and isinstance(value, str) else json_schema(value)
        for key, value in schema.items()
    }


def ollama_messages(system: str, contents: list) -> list[dict]:
    messages = [{"role": "system", "content": system}]
    for content in contents:
        role = "assistant" if content.role == "model" else content.role
        text = ""
        calls = []
        for part in content.parts or []:
            if part.text:
                text += part.text
            if part.function_call:
                calls.append(
                    {
                        "function": {
                            "name": part.function_call.name,
                            "arguments": dict(part.function_call.args or {}),
                        }
                    }
                )
            if part.function_response:
                messages.append(
                    {
                        "role": "tool",
                        "tool_name": part.function_response.name,
                        "content": json.dumps(part.function_response.response),
                    }
                )
        if role != "tool":
            item = {"role": role, "content": text}
            if calls:
                item["tool_calls"] = calls
            messages.append(item)
    return messages


class OllamaAdapter:
    def __init__(self, host: str, tool_mode="native"):
        self.host = host.rstrip("/")
        self.tool_mode = tool_mode
        self.aio = SimpleNamespace(models=self)

    async def generate_content(self, *, model, contents, config, tool_catalog=None):
        functions = [function for tool in config.tools for function in tool.function_declarations]

        def describe(items):
            return [
                {
                    "type": "function",
                    "function": {
                        "name": f.name,
                        "description": f.description,
                        "parameters": json_schema(f.parameters.model_dump(mode="json", exclude_none=True)),
                    },
                }
                for f in items
            ]

        tools = describe(functions)
        messages = ollama_messages(config.system_instruction, contents)
        payload = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.1, "num_predict": 600, "num_ctx": 16384},
        }
        if self.tool_mode == "json":
            # Explicit local-provider protocol, not a model fallback. The model still selects
            # every tool and argument; constrained decoding replaces native tool parsing.
            payload.pop("tools")
            payload["format"] = {
                "type": "object",
                "properties": {
                    "tool_calls": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 4,
                        "items": {
                            "anyOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "enum": [t["function"]["name"]]},
                                        "arguments": t["function"]["parameters"],
                                    },
                                    "required": ["name", "arguments"],
                                    "additionalProperties": False,
                                }
                                for t in tools
                            ]
                        },
                    }
                },
                "required": ["tool_calls"],
                "additionalProperties": False,
            }
            messages[0]["content"] += (
                "\nReturn only a JSON object with tool_calls: an array of {name, arguments}. Available tool definitions:\n"
                + json.dumps(describe(tool_catalog or functions))
            )
            for item in messages[1:]:
                if item.get("tool_calls"):
                    item["content"] = json.dumps(
                        {
                            "tool_calls": [
                                {"name": c["function"]["name"], "arguments": c["function"]["arguments"]}
                                for c in item.pop("tool_calls")
                            ]
                        }
                    )
                if item["role"] == "tool":
                    item["role"] = "user"
                    item["content"] = f"Tool result from {item.pop('tool_name')}: {item['content']}"
            # Keep the catalog prefix stable. Current authorization stays in constrained
            # decoding plus a small final reminder, rather than rewriting the system text.
            available = {
                f.name: {
                    name: list(schema.enum)
                    for name, schema in (f.parameters.properties or {}).items()
                    if schema.enum
                }
                for f in functions
            }
            messages.append(
                {
                    "role": "user",
                    "content": "Available tools and allowed parameter values for this call: "
                    + json.dumps(available),
                }
            )
        try:
            async with httpx.AsyncClient(timeout=280) as client:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                message = response.json()["message"]
                if self.tool_mode == "json":
                    structured = json.loads(message["content"])
                    message = {
                        "tool_calls": [
                            {"function": {"name": c["name"], "arguments": c["arguments"]}}
                            for c in structured["tool_calls"]
                        ]
                    }
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise DomainError(
                "The selected Ollama model is unavailable. Start Ollama and pull the configured "
                "tool-capable model; no paid provider fallback was used.",
                503,
                "model_unavailable",
            ) from exc
        parts = []
        for call in message.get("tool_calls", []):
            function = call["function"]
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            parts.append(types.Part(function_call=types.FunctionCall(name=function["name"], args=arguments)))
        if message.get("content"):
            parts.append(types.Part.from_text(text=message["content"]))
        return types.GenerateContentResponse(
            candidates=[types.Candidate(content=types.Content(role="model", parts=parts))]
        )
