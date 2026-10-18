import asyncio
from dataclasses import replace
from types import SimpleNamespace

from google.genai import types

from ripple.agent import Agent, bounded_declarations, declarations, pending_declarations
from ripple.models import DomainError


def test_native_function_loop_produces_a_cited_action_without_executing_it(service, settings):
    workspace = "c" * 32
    service.load(workspace, "memory")
    run = service.start(workspace)
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        record = service.get_run(workspace, run["id"])
        probe_id = next(
            source["id"]
            for source in service.repo.sources(workspace)
            if source.get("service") == "payments" and source["id"] in record["seen_evidence"]
        )
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
    assert final["model_calls"] == 1
    receipts = final["completed_tools"]
    assert {r["arguments"]["service"] for r in receipts if r["name"] == "probe_service"} == {
        "storefront",
        "checkout",
        "payments",
        "inventory",
        "ledger",
        "notifications",
    }
    assert all(r["origin"] == "application_preflight" for r in receipts)
    assert any(r["name"] == "get_impact" and r["arguments"]["service"] == "payments" for r in receipts)
    assert "automatic preload is not a previous model decision" in calls[0]["contents"][0].parts[-1].text
    assert service.repo.read(workspace)["simulator"]["executions"] == 0
    assert calls[-1]["config"].automatic_function_calling.disable
    assert calls[-1]["config"].max_output_tokens == 4096
    assert calls[-1]["config"].thinking_config.thinking_level == "LOW"
    assert final["provider_receipts"][0]["tool_names"] == ["propose_action"]
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
    packet = calls[0]["contents"][0].parts[-1].text
    assert "incident_memory" not in packet and "dependency_impacts" not in packet
    assert len([r for r in baseline["completed_tools"] if r["name"] == "probe_service"]) == 6


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


def test_truncated_native_response_stops_without_accepting_an_action(service, settings):
    workspace = "9" * 32
    service.load(workspace, "memory")
    run = service.start(workspace)

    async def generate(**kwargs):
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    finish_reason="MAX_TOKENS",
                    content=types.Content(
                        role="model", parts=[types.Part.from_text(text="Incomplete response")]
                    ),
                )
            ]
        )

    agent = Agent(service, settings)
    agent.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
    asyncio.run(agent.run(workspace, run["id"]))
    final = service.get_run(workspace, run["id"])
    assert final["status"] == "interrupted" and final["model_calls"] == 1
    assert "token limit" in final["error"] and final["proposals"] == []
    assert final["provider_receipts"][0]["finish_reason"] == "MAX_TOKENS"
    assert service.repo.read(workspace)["simulator"]["executions"] == 0


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
                    "summary": "This scripted provider deliberately submits an invented citation to test the independent guard.",
                    "evidence_ids": ["invented-source"],
                    "affected_services": ["payments"],
                },
            )
        else:
            call = types.FunctionCall(
                name="submit_diagnosis",
                args={
                    "summary": "The invented citation was rejected; preserve observations and request diagnostic traces.",
                    "affected_services": ["checkout"],
                    "evidence_ids": ["flag-config"],
                    "missing_evidence": ["Correlated diagnostic traces"],
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


def test_conclusion_schemas_allow_only_retrieved_citations_in_both_modes():
    seen = ["alert", "flag-config", "memory-actual-outcome", "probe-current-target"]
    receipts = [{"name": "probe_service", "arguments": {"service": "payments"}}]
    for mode in ("graph", "baseline"):
        functions = pending_declarations(declarations(mode), receipts, seen)
        for function in functions:
            if function.name in {"propose_action", "submit_diagnosis"}:
                assert set(function.parameters.properties["evidence_ids"].items.enum) == set(seen)
                assert "invented-source" not in function.parameters.properties["evidence_ids"].items.enum


def test_partial_preflight_graph_failure_preserves_probes_without_calling_model(
    service, settings, monkeypatch
):
    workspace = "f" * 32
    service.load(workspace, "memory")
    run = service.start(workspace)
    called = []

    def unavailable(*args):
        raise DomainError("Native traversal unavailable", 503, "graph_unavailable")

    async def forbidden(**kwargs):
        called.append(kwargs)
        raise AssertionError("Model must not run after graph preflight fails")

    monkeypatch.setattr(service.repo, "impact", unavailable)
    agent = Agent(service, settings)
    agent.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=forbidden)))
    asyncio.run(agent.run(workspace, run["id"]))
    result = service.get_run(workspace, run["id"])
    assert not called and result["status"] == "interrupted"
    assert result["model_calls"] == 0 and not result["proposals"]
    assert len([sid for sid in result["seen_evidence"] if sid.startswith("probe-")]) == 6
    assert service.repo.read(workspace)["simulator"]["executions"] == 0
