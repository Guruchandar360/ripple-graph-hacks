import asyncio
from dataclasses import replace
from types import SimpleNamespace

from google.genai import types

from ripple.agent import Agent, declarations


def test_native_function_loop_produces_a_cited_action_without_executing_it(service, settings):
    workspace = "c" * 32
    service.load(workspace, "memory")
    run = service.start(workspace)
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        step = len(calls)
        if step == 1:
            fc = types.FunctionCall(name="get_context", args={})
        elif step == 2:
            fc = types.FunctionCall(name="probe_service", args={"service": "payments"})
        else:
            record = service.get_run(workspace, run["id"])
            probe_id = next(sid for sid in record["seen_evidence"] if sid.startswith("probe-"))
            fc = types.FunctionCall(
                name="propose_action",
                args={
                    "action": "disable_feature_flag",
                    "target": "payments",
                    "summary": "The current flag rejects legacy currency.",
                    "evidence_ids": ["flag-config", probe_id],
                    "affected_services": ["storefront", "checkout", "payments"],
                },
            )
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(content=types.Content(role="model", parts=[types.Part(function_call=fc)]))
            ]
        )

    agent = Agent(service, settings)
    agent.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
    asyncio.run(agent.run(workspace, run["id"]))
    final = service.get_run(workspace, run["id"])
    assert final["status"] == "awaiting_approval"
    assert final["model_calls"] == 3
    assert service.repo.read(workspace)["simulator"]["executions"] == 0
    assert calls[-1]["config"].automatic_function_calling.disable


def test_no_terminal_tool_result_hits_turn_limit_and_keeps_evidence(service, settings):
    workspace = "d" * 32
    service.load(workspace, "outdated-fix")
    run = service.start(workspace)

    async def generate(**kwargs):
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(function_call=types.FunctionCall(name="get_context", args={}))],
                    )
                )
            ]
        )

    agent = Agent(service, replace(settings, max_turns=2))
    agent.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
    asyncio.run(agent.run(workspace, run["id"]))
    final = service.get_run(workspace, run["id"])
    assert final["status"] == "interrupted"
    assert final["model_calls"] == 2
    assert "flag-config" in final["seen_evidence"]
    assert final["proposals"] == []


def test_baseline_provider_schema_does_not_expose_graph_or_memory():
    names = {f.name for f in declarations("baseline")}
    assert {"get_context", "probe_service", "propose_action"} <= names
    assert not names & {"get_impact", "retrieve_memory"}
