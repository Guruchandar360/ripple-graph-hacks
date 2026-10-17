from concurrent.futures import ThreadPoolExecutor

import pytest

from ripple import simulator
from ripple.fixtures import DEPENDENCIES
from ripple.models import DomainError
from ripple.repository import projection

WS = "a" * 32


def investigate(service, scenario="memory", workspace=WS):
    service.load(workspace, scenario)
    run = service.start(workspace)
    service.tool(workspace, run["id"], "get_context", {})
    probe = service.tool(workspace, run["id"], "probe_service", {"service": "payments"})
    return run, probe["evidence_ids"][0]


def propose(service, run, probe_id, action="disable_feature_flag", workspace=WS):
    return service.tool(
        workspace,
        run["id"],
        "propose_action",
        {
            "action": action,
            "target": "payments",
            "summary": "Current probes and runtime config support this action.",
            "evidence_ids": [probe_id, "flag-config"],
        },
    )


def test_flag_action_changes_actual_simulator_state_and_verifies_impact(service, repo):
    run, pid = investigate(service)
    proposal = propose(service, run, pid)
    result = service.execute(WS, run["id"], proposal["action_id"])
    assert result["verified"]
    assert {p["service"] for p in result["after"]} == {"payments", "checkout", "storefront"}
    assert all(not p["healthy"] for p in result["before"])
    assert all(p["healthy"] for p in result["after"])
    assert repo.read(WS)["simulator"]["strict_currency_validation"] is False


def test_new_evidence_invalidates_previously_approved_action(service, repo):
    run, pid = investigate(service, "outdated-fix")
    proposal = propose(service, run, pid, "rollback_deployment")
    service.inject(WS, run["id"])
    with pytest.raises(DomainError, match="approval is stale"):
        service.execute(WS, run["id"], proposal["action_id"])
    assert repo.read(WS)["simulator"]["executions"] == 0
    assert service.get_run(WS, run["id"])["status"] == "evidence_changed"


def test_reinvestigate_after_migration_retains_compatible_recovery(service):
    run, pid = investigate(service, "outdated-fix")
    propose(service, run, pid, "rollback_deployment")
    service.inject(WS, run["id"])
    fresh = service.start(WS)
    assert fresh["revalidates_run_id"] == run["id"]
    assert fresh["previous_recommendation"]["action"] == "rollback_deployment"
    assert fresh["seen_evidence"] == ["alert"]
    service.tool(WS, fresh["id"], "get_context", {})
    probe = service.tool(WS, fresh["id"], "probe_service", {"service": "payments"})
    proposal = propose(service, fresh, probe["evidence_ids"][0])
    assert service.execute(WS, fresh["id"], proposal["action_id"])["verified"]


def test_duplicate_and_concurrent_approval_execute_once(service, repo):
    run, pid = investigate(service)
    proposal = propose(service, run, pid)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: service.execute(WS, run["id"], proposal["action_id"]), range(4)))
    assert all(r == results[0] for r in results)
    assert repo.read(WS)["simulator"]["executions"] == 1
    assert len(repo.read(WS)["memory"]) == 1


def test_old_advisory_proposal_is_still_checked_against_physical_runtime(service, repo):
    run, pid = investigate(service, "outdated-fix")
    result = propose(service, run, pid, "rollback_deployment")
    assert result["accepted"]
    with pytest.raises(DomainError, match="Runtime precondition failed"):
        service.execute(WS, run["id"], result["action_id"])
    assert repo.read(WS)["simulator"]["executions"] == 0


def test_current_migration_explicitly_blocks_old_rollback(service):
    run, pid = investigate(service, "memory")
    result = propose(service, run, pid, "rollback_deployment")
    assert "schema 2" in result["blocked_reason"]


def test_runtime_also_rejects_incompatible_rollback():
    with pytest.raises(DomainError, match="Runtime precondition failed"):
        simulator.execute(simulator.seed("outdated-fix"), "rollback_deployment", "payments")


def test_restart_is_not_reported_as_recovery_when_it_does_not_fix_fault(service, repo):
    run, pid = investigate(service)
    proposal = propose(service, run, pid, "restart_service")
    result = service.execute(WS, run["id"], proposal["action_id"])
    assert not result["verified"]
    assert service.get_run(WS, run["id"])["status"] == "recovery_failed"
    assert repo.memories(WS)[0]["verified"] is False


def test_memory_survives_new_scenario_without_conversation_carryover(service):
    run, pid = investigate(service)
    proposal = propose(service, run, pid)
    service.execute(WS, run["id"], proposal["action_id"])
    service.load(WS, "memory")
    fresh = service.start(WS)
    assert fresh["seen_evidence"] == ["alert"]
    result = service.tool(WS, fresh["id"], "retrieve_memory", {})
    assert len(result["outcomes"]) == 1
    assert result["outcomes"][0]["verified"]
    assert service.get_run(WS, fresh["id"])["memory_ids"] == [proposal["action_id"]]


def test_insufficient_evidence_blocks_remediation_and_accepts_honest_diagnosis(service, repo):
    run, pid = investigate(service, "insufficient")
    result = service.tool(
        WS,
        run["id"],
        "propose_action",
        {
            "action": "restart_service",
            "target": "payments",
            "summary": "Attempt a restart using current probe.",
            "evidence_ids": [pid],
        },
    )
    assert not result["accepted"]
    service.tool(
        WS,
        run["id"],
        "submit_diagnosis",
        {
            "summary": "Origin telemetry is missing. A root cause is not established.",
            "affected_services": ["checkout", "storefront"],
            "evidence_ids": ["telemetry-gap"],
            "missing_evidence": ["Origin logs and request traces"],
        },
    )
    assert service.get_run(WS, run["id"])["status"] == "needs_evidence"
    assert repo.read(WS)["simulator"]["executions"] == 0


def test_citations_must_be_retrieved_and_active(service, repo):
    run, pid = investigate(service, "outdated-fix")
    for invalid in ["invented-source", "migration"]:
        with pytest.raises(DomainError, match="actually retrieved"):
            service.tool(
                WS,
                run["id"],
                "propose_action",
                {
                    "action": "disable_feature_flag",
                    "target": "payments",
                    "summary": "Try disabling a supported flag.",
                    "evidence_ids": [invalid],
                },
            )
    state = repo.read(WS)
    state["sources"] = [{**s, "active": False} if s["id"] == "flag-config" else s for s in state["sources"]]
    repo.save(WS, state)
    with pytest.raises(DomainError, match="active evidence"):
        propose(service, run, pid)


def test_workspace_isolation_for_runs_actions_and_memory(service, repo):
    run, _pid = investigate(service)
    other = "b" * 32
    service.load(other, "memory")
    with pytest.raises(DomainError, match="Run not found"):
        service.get_run(other, run["id"])
    assert repo.memories(other) == []


def test_scenario_reload_invalidates_old_proposal(service):
    run, pid = investigate(service)
    proposal = propose(service, run, pid)
    service.load(WS, "outdated-fix")
    with pytest.raises(DomainError, match="Scenario changed"):
        service.execute(WS, run["id"], proposal["action_id"])


def test_graph_outage_does_not_run_actions_or_substitute_state(service, repo):
    run, pid = investigate(service)
    proposal = propose(service, run, pid)
    repo.online = False
    with pytest.raises(DomainError, match="offline"):
        service.execute(WS, run["id"], proposal["action_id"])
    repo.online = True
    assert repo.read(WS)["simulator"]["executions"] == 0


def test_only_one_investigation_can_be_active(service):
    investigate(service)
    with pytest.raises(DomainError, match="already running"):
        service.start(WS)


def test_baseline_gets_all_documents_but_no_graph_or_memory_tools(service):
    service.load(WS, "memory")
    run = service.start(WS, "baseline")
    context = service.tool(WS, run["id"], "get_context", {})
    assert {s["id"] for s in context["sources"]} >= {"topology", "migration", "flag-config", "old-runbook"}
    for tool in ["get_impact", "retrieve_memory"]:
        with pytest.raises(DomainError, match="disabled"):
            service.tool(WS, run["id"], tool, {})


def test_projection_preserves_constraint_provenance_and_actual_probe_relationships(service, repo):
    run, pid = investigate(service, "memory")
    proposal = propose(service, run, pid)
    service.execute(WS, run["id"], proposal["action_id"])
    nodes, edges = projection(repo.read(WS))
    assert len({n["id"] for n in nodes}) == len(nodes)
    assert {e["kind"] for e in edges} >= {"SUPPORTED_BY", "DEPENDS_ON", "EXECUTED", "VERIFIED_BY"}
    assert any(n["label"] == "Constraint" for n in nodes)


def test_dependency_probe_propagation_excludes_unrelated_services():
    runtime = simulator.seed("outdated-fix")
    dependencies = [list(e) for e in DEPENDENCIES]
    assert not simulator.probe(runtime, "storefront", dependencies)["healthy"]
    assert simulator.probe(runtime, "inventory", dependencies)["healthy"]
    assert simulator.probe(runtime, "ledger", dependencies)["healthy"]


def test_healthy_unrelated_target_cannot_manufacture_a_recovery(service, repo):
    run, _pid = investigate(service)
    state = repo.read(WS)
    state["dependencies"] = [edge for edge in state["dependencies"] if edge[1] != "notifications"]
    repo.save(WS, state)
    probe = service.tool(WS, run["id"], "probe_service", {"service": "notifications"})
    proposal = service.tool(
        WS,
        run["id"],
        "propose_action",
        {
            "action": "restart_service",
            "target": "notifications",
            "summary": "This is a deliberately irrelevant restart.",
            "evidence_ids": probe["evidence_ids"],
        },
    )
    result = service.execute(WS, run["id"], proposal["action_id"])
    assert not result["verified"]
    assert any(p["service"] == "checkout" and not p["healthy"] for p in result["after"])


def test_action_receipt_supersedes_old_flag_and_probe_evidence(service, repo):
    run, pid = investigate(service)
    proposal = propose(service, run, pid)
    service.execute(WS, run["id"], proposal["action_id"])
    active = {s["id"] for s in repo.context(WS)["sources"]}
    assert "flag-config" not in active
    assert pid not in active
    assert f"after-{proposal['action_id']}" in active


def test_history_archives_real_graph_projection_before_scenario_replacement(service):
    run, pid = investigate(service)
    proposal = propose(service, run, pid)
    service.execute(WS, run["id"], proposal["action_id"])
    original = service.get_run(WS, run["id"])["graph_snapshot"]
    service.load(WS, "insufficient")
    history = service.get_run(WS, run["id"])
    assert history["graph_snapshot"] == original
    assert any(n["id"] == "old-runbook" for n in original["nodes"])


def test_a_failed_attempt_can_be_followed_by_an_evidence_supported_flag_fix(service):
    run, pid = investigate(service)
    proposal = propose(service, run, pid, "restart_service")
    assert not service.execute(WS, run["id"], proposal["action_id"])["verified"]
    fresh = service.start(WS)
    context = service.tool(WS, fresh["id"], "get_context", {})
    receipt = next(s["id"] for s in context["sources"] if s.get("record_type") == "runtime_config")
    probe = service.tool(WS, fresh["id"], "probe_service", {"service": "payments"})
    fix = service.tool(
        WS,
        fresh["id"],
        "propose_action",
        {
            "action": "disable_feature_flag",
            "target": "payments",
            "summary": "The failed restart left validation enabled.",
            "evidence_ids": [receipt, *probe["evidence_ids"]],
        },
    )
    assert fix["accepted"]
    assert service.execute(WS, fresh["id"], fix["action_id"])["verified"]
