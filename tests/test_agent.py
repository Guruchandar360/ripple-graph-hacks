import asyncio
from dataclasses import replace
from types import SimpleNamespace

from google.genai import types

from ripple.agent import Agent, bounded_declarations, declarations


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
    assert sum(e.get("origin") == "application_preflight" for e in final["events"]) == 2
    assert "automatic preload is not a previous model decision" in calls[0]["contents"][0].parts[-1].text
    assert service.repo.read(workspace)["simulator"]["executions"] == 0
    assert calls[-1]["config"].automatic_function_calling.disable
    # A fresh conversation receives persisted outcomes without replaying earlier chat.
    service.execute(workspace, run["id"], final["proposals"][-1]["id"])
    outcome_id = service.repo.read(workspace)["memory"][-1]["id"]
    service.load(workspace, "memory")
    run = service.start(workspace)
    calls.clear()
    asyncio.run(agent.run(workspace, run["id"]))
    fresh = service.get_run(workspace, run["id"])
    assert outcome_id in fresh["memory_ids"]
    assert f"memory-{outcome_id}" in calls[0]["contents"][0].parts[-1].text
    assert fresh["status"] == "awaiting_approval"

    service.load(workspace, "memory")
    run = service.start(workspace, "baseline")
    calls.clear()
    asyncio.run(agent.run(workspace, run["id"]))
    baseline = service.get_run(workspace, run["id"])
    assert not baseline["memory_ids"]
    assert "incident_memory" not in calls[0]["contents"][0].parts[-1].text


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
    for function in declarations("graph"):
        key = (
            "service"
            if function.name in {"probe_service", "get_impact"}
            else "target"
            if function.name == "propose_action"
            else None
        )
        if key:
            assert set(function.parameters.properties[key].enum) == {
                "storefront",
                "checkout",
                "payments",
                "ledger",
                "inventory",
                "notifications",
            }


def test_current_retrieved_global_blocks_remove_proposal_but_unseen_policies_do_not():
    policies = [
        {"action": action, "allowed": False, "target": "*", "source_id": "constraint-source"}
        for action in ("rollback_deployment", "disable_feature_flag", "restart_service")
    ]
    available, blocked = bounded_declarations("graph", 7, policies, [])
    assert not blocked and "propose_action" in {f.name for f in available}
    available, blocked = bounded_declarations("graph", 7, policies, ["constraint-source"])
    assert blocked and [f.name for f in available] == ["submit_diagnosis"]
    policies[0]["target"] = "payments"
    available, blocked = bounded_declarations("graph", 7, policies, ["constraint-source"])
    assert not blocked and "propose_action" in {f.name for f in available}


def test_last_two_turns_reserve_structured_conclusion_without_selecting_an_action():
    available, blocked = bounded_declarations("baseline", 2, [], [])
    assert not blocked
    assert {f.name for f in available} == {"propose_action", "submit_diagnosis"}


def test_rejected_model_proposal_preserves_evidence_and_can_finish_honestly(service, settings):
    workspace = "e" * 32
    service.load(workspace, "memory")
    run = service.start(workspace)
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            call = types.FunctionCall(
                name="propose_action",
                args={
                    "action": "disable_feature_flag",
                    "target": "payments",
                    "summary": "The flag configuration suggests a mitigation, but no target probe was run.",
                    "evidence_ids": ["flag-config"],
                    "affected_services": ["payments"],
                },
            )
        else:
            call = types.FunctionCall(
                name="submit_diagnosis",
                args={
                    "summary": "The current evidence needs a target probe before an action can be justified.",
                    "affected_services": ["checkout"],
                    "evidence_ids": ["flag-config"],
                    "missing_evidence": ["Current payments request probe"],
                },
            )
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(content=types.Content(role="model", parts=[types.Part(function_call=call)]))
            ]
        )

    agent = Agent(service, settings)
    agent.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
    asyncio.run(agent.run(workspace, run["id"]))
    final = service.get_run(workspace, run["id"])
    assert final["status"] == "needs_evidence"
    assert any(e["title"] == "Tool request rejected" for e in final["events"])
    assert "flag-config" in final["seen_evidence"]
    assert not final["proposals"]
    assert service.repo.read(workspace)["simulator"]["executions"] == 0

