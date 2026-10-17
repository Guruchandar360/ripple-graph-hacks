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
    def __init__(self, host: str):
        self.host = host.rstrip("/")
        self.aio = SimpleNamespace(models=self)

    async def generate_content(self, *, model, contents, config):
        functions = [function for tool in config.tools for function in tool.function_declarations]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": f.name,
                    "description": f.description,
                    "parameters": json_schema(f.parameters.model_dump(mode="json", exclude_none=True)),
                },
            }
            for f in functions
        ]
        try:
            async with httpx.AsyncClient(timeout=280) as client:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": model,
                        "messages": ollama_messages(config.system_instruction, contents),
                        "tools": tools,
                        "stream": False,
                        "think": False,
                        "options": {"temperature": 0.1, "num_predict": 600, "num_ctx": 16384},
                    },
                )
                response.raise_for_status()
                message = response.json()["message"]
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
