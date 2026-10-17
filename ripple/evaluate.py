"""Run actual model evaluations; no canned scores or mock provider fallbacks.

Example: python -m ripple.evaluate --cases 1 --mode both
"""

import argparse
import asyncio
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from ripple.agent import Agent
from ripple.config import Settings
from ripple.evidence import resolve_sources
from ripple.fixtures import migration_source, source
from ripple.models import DomainError, now
from ripple.repository import GraphRepository
from ripple.service import RippleService


@dataclass(frozen=True)
class Case:
    name: str
    scenario: str = "outdated-fix"
    variant: str = ""
    expect: str = "recovered"


CASES = [
    Case("Migration already known", variant="migration"),
    Case("Evidence arrives after recommendation", variant="late"),
    Case("Effective time beats ingestion order", variant="shuffled"),
    Case("Additional downstream impact", variant="extra_dependency"),
    Case("Unrelated telemetry is not impact", variant="unrelated"),
    Case("Failed restart is not successful memory", variant="failed_restart"),
    Case("Verified previous outcome", "memory", "memory"),
    Case("Fresh conversation uses persistent memory", "memory", "fresh"),
    Case(
        "Remembered procedure conflicts with current context",
        "insufficient",
        "incompatible",
        "needs_evidence",
    ),
    Case("Missing origin diagnostics", "insufficient", "", "needs_evidence"),
    Case("Misleading runbook does not prove cause", "insufficient", "misleading", "needs_evidence"),
    Case("Superseded ownership is excluded", "insufficient", "ownership", "needs_evidence"),
]


def bootstrap_memory(service, workspace, failed=False):
    service.load(workspace, "memory")
    run = service.start(workspace)
    service.tool(workspace, run["id"], "get_context", {})
    probe = service.tool(workspace, run["id"], "probe_service", {"service": "payments"})
    action = service.tool(
        workspace,
        run["id"],
        "propose_action",
        {
            "action": "restart_service" if failed else "disable_feature_flag",
            "target": "payments",
            "summary": "Evaluator bootstrap: measured historical simulator outcome, not a model decision.",
            "evidence_ids": ["flag-config", *probe["evidence_ids"]],
        },
    )
    service.execute(workspace, run["id"], action["action_id"])


def prepare(service, workspace, case):
    if case.variant in {"memory", "fresh", "incompatible", "failed_restart"}:
        bootstrap_memory(service, workspace, failed=case.variant == "failed_restart")
    service.load(workspace, case.scenario)
    state = service.repo.read(workspace)
    if case.scenario == "outdated-fix" and case.variant != "late":
        state["sources"].append(migration_source())
    if case.variant == "shuffled":
        state["sources"].reverse()
        # A stale document arriving later must remain historical, not become current by arrival time.
        state["sources"].append(
            source(
                "schema-1-stale",
                "Historical migration record",
                "Ledger used schema 1 last month; this record is superseded by migration.",
                "2026-09-01T00:00:00Z",
                active=False,
                superseded_by="migration",
            )
        )
    if case.variant == "extra_dependency":
        state["dependencies"].append(["notifications", "checkout"])
        catalog = next(s for s in state["sources"] if s["id"] == "topology")
        catalog["text"] += " Notifications also depends directly on checkout."
    if case.variant == "unrelated":
        state["sources"].append(
            source(
                "unrelated-alert",
                "Inventory monitor",
                "An unrelated inventory queue warning occurred before this deployment. "
                "Its request probe is passing; do not infer payments dependencies from co-occurrence.",
                now(),
            )
        )
    if case.variant == "misleading":
        state["sources"].append(
            source(
                "uncorroborated-runbook",
                "Generic operator suggestion",
                "A past operator suggested restarting payments for HTTP 503. This suggestion has no "
                "supporting request trace or confirmed cause for the current incident.",
                now(),
            )
        )
    if case.variant == "ownership":
        state["sources"].append(
            source(
                "old-owner",
                "Old service catalog",
                "Experience owned checkout in August. This entry is superseded by the current catalog.",
                "2026-08-01T00:00:00Z",
                active=False,
                superseded_by="topology",
            )
        )
    state["sources"] = resolve_sources(state["sources"])
    state["revision"] += 1
    service.repo.save(workspace, state)


async def measure(service, agent, case, mode, index):
    workspace = uuid.uuid4().hex
    prepare(service, workspace, case)
    run = service.start(workspace, mode)
    await agent.run(workspace, run["id"])
    result = service.get_run(workspace, run["id"])
    stale_rejected = None
    if case.variant == "late" and result["status"] != "interrupted":
        pending = next((p for p in result["proposals"] if not p["blocked_reason"]), None)
        service.inject(workspace, run["id"])
        if pending:
            try:
                service.execute(workspace, run["id"], pending["id"])
                stale_rejected = False
            except DomainError as exc:
                stale_rejected = exc.code == "stale_action"
        previous_calls, previous_ms = result["model_calls"], result["elapsed_ms"]
        run = service.start(workspace, mode)
        await agent.run(workspace, run["id"])
        result = service.get_run(workspace, run["id"])
        result["model_calls"] += previous_calls
        result["elapsed_ms"] += previous_ms
    action = next(
        (p for p in reversed(result["proposals"]) if not p["blocked_reason"] and not p["stale"]), None
    )
    if action and result["status"] == "awaiting_approval":
        try:
            service.execute(workspace, run["id"], action["id"])
        except DomainError:
            pass
    final = service.get_run(workspace, run["id"])
    state = service.repo.read(workspace)
    reported = set((final["diagnosis"] or {}).get("affected_services", []))
    if action:
        reported = set(action.get("affected_services", []))
    expected_impact = {"storefront", "checkout", "payments"}
    if case.variant == "extra_dependency":
        expected_impact |= {"notifications", "inventory"}
    if case.scenario == "insufficient":
        expected_impact = {"checkout", "storefront"}
    citations = [sid for p in final["proposals"] for sid in p["evidence_ids"]]
    citations += (final["diagnosis"] or {}).get("evidence_ids", [])
    row = {
        "case": f"C{index:02d}",
        "name": case.name,
        "mode": mode,
        "status": final["status"],
        "verified": final["status"] == "recovered",
        "expected_met": final["status"] == case.expect,
        "valid_citations": bool(citations) and set(citations).issubset(final["seen_evidence"]),
        "correct_impact": reported == expected_impact,
        "model_calls": result["model_calls"],
        "elapsed_ms": result["elapsed_ms"],
        "invalid_proposals": sum(bool(p["blocked_reason"]) for p in final["proposals"]),
        "executed_violations": sum(bool(p["result"] and p["blocked_reason"]) for p in final["proposals"]),
        "stale_approval_rejected": stale_rejected,
        "error": final["error"],
    }
    if case.variant == "ownership":
        retrieved = [s for s in service.repo.context(workspace)["sources"] if s["id"] == "old-owner"]
        row["superseded_owner_excluded"] = not retrieved
        row["expected_met"] &= not retrieved
    if case.variant == "late":
        row["expected_met"] &= stale_rejected is True
    replay = {
        **final,
        "replay": True,
        "scenario": state["scenario"],
        "graph": service.repo.graph(workspace),
        "label": "Actual model run against the executable synthetic simulator",
    }
    return row, replay


async def evaluate(args):
    settings = Settings()
    if not settings.model_configured:
        raise SystemExit("GEMINI_API_KEY is required. No benchmark was run and no scores were generated.")
    repo = GraphRepository(settings)
    repo.health()
    service = RippleService(repo, settings)
    agent = Agent(service, settings)
    rows, replay_records = [], []
    modes = ["graph", "baseline"] if args.mode == "both" else [args.mode]
    for index, case in enumerate(CASES[: args.cases], 1):
        for mode in modes:
            print(f"Running C{index:02d} / {mode}: {case.name}", flush=True)
            row, replay = await measure(service, agent, case, mode, index)
            rows.append(row)
            replay_records.append(replay)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "measured": bool(rows),
        "created_at": now(),
        "model": settings.active_model,
        "model_provider": settings.provider,
        "cases": rows,
        "summary": {
            "runs": len(rows),
            "expected_met": sum(r["expected_met"] for r in rows),
            "verified_recoveries": sum(r["verified"] for r in rows),
        },
        "limitations": "Synthetic fixtures; small sample; bootstrap memory is a measured simulator outcome, "
        "not model-generated history. Baseline has documents but no incident-memory retrieval.",
    }
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    replay_dir = output.parent / "replays"
    replay_dir.mkdir(exist_ok=True)
    for record in replay_records:
        (replay_dir / f"{record['id']}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} actual evaluation runs to {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, choices=range(1, 13), default=1)
    parser.add_argument("--mode", choices=["graph", "baseline", "both"], default="both")
    parser.add_argument("--output", default="artifacts/evaluations.json")
    asyncio.run(evaluate(parser.parse_args()))


if __name__ == "__main__":
    main()
