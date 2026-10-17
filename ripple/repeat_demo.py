"""Three sequential real-model demonstrations, including memory from actual prior model actions."""

import asyncio
import json
import uuid
from pathlib import Path

from ripple.agent import Agent
from ripple.config import Settings
from ripple.models import DomainError, now
from ripple.repository import GraphRepository
from ripple.service import RippleService


async def demonstrate():
    settings = Settings()
    repo = GraphRepository(settings)
    repo.health()
    service, rows = RippleService(repo, settings), []
    agent = Agent(service, settings)
    destination = Path("artifacts/repeatability")
    (destination / "replays").mkdir(parents=True, exist_ok=True)

    async def investigate(workspace, execute=True):
        run = service.start(workspace)
        await agent.run(workspace, run["id"])
        current = service.get_run(workspace, run["id"])
        action = next(
            (p for p in reversed(current["proposals"]) if not p["blocked_reason"] and not p["stale"]), None
        )
        if execute and action and current["status"] == "awaiting_approval":
            try:
                service.execute(workspace, current["id"], action["id"])
            except DomainError:
                pass
        return service.get_run(workspace, run["id"])

    def save(workspace, run, phase, repetition, prior=None):
        record = {
            **run,
            "replay": True,
            "graph": repo.graph(workspace),
            "scenario": repo.read(workspace)["scenario"],
            "demonstration_phase": phase,
            "repetition": repetition,
            "evaluation_case": {"recovery": "C02", "memory": "C08", "insufficient": "C10"}[phase],
            "label": f"Actual model demonstration {repetition}: {phase}; memory comes from actual earlier model actions",
        }
        if prior:
            record["events"] = [
                {**e, "id": i, "source_run_id": r["id"]}
                for i, (r, e) in enumerate(((r, e) for r in (prior, run) for e in r["events"]), 1)
            ]
            record["proposals"] = prior["proposals"] + run["proposals"]
            record["model_calls"] += prior["model_calls"]
            record["elapsed_ms"] += prior["elapsed_ms"]
        (destination / "replays" / f"{run['id']}.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )

    for repetition in range(1, 4):
        workspace = uuid.uuid4().hex
        service.load(workspace, "outdated-fix")
        initial = await investigate(workspace, execute=False)
        initial_usable = initial["status"] in {"awaiting_approval", "needs_evidence", "complete"}
        pending = next((p for p in initial["proposals"] if not p["blocked_reason"]), None)
        service.inject(workspace, initial["id"])
        initial = service.get_run(workspace, initial["id"])
        stale_rejected = None
        if pending:
            try:
                service.execute(workspace, initial["id"], pending["id"])
                stale_rejected = False
            except DomainError as exc:
                stale_rejected = exc.code == "stale_action"
        recovery = await investigate(workspace)
        save(workspace, recovery, "recovery", repetition, prior=initial)
        learned = {m["id"] for m in repo.read(workspace)["memory"] if m["verified"]}
        service.load(workspace, "memory")
        memory = await investigate(workspace)
        memory_used = bool(learned & set(memory["memory_ids"]))
        cited = {
            sid.removeprefix("memory-")
            for proposal in memory["proposals"]
            for sid in proposal["evidence_ids"]
            if sid.startswith("memory-")
        }
        save(workspace, memory, "memory", repetition)
        service.load(workspace, "insufficient")
        insufficient = await investigate(workspace, execute=False)
        no_execution = repo.read(workspace)["simulator"]["executions"] == 0
        save(workspace, insufficient, "insufficient", repetition)
        row = {
            "repetition": repetition,
            "initial_investigation_completed": initial_usable,
            "recovery": recovery["status"],
            "memory": memory["status"],
            "actual_previous_model_outcome_retrieved": memory_used,
            "actual_previous_model_outcome_cited": bool(learned & cited),
            "memory_loading": "application_preflight",
            "insufficient_evidence": insufficient["status"],
            "no_unjustified_execution": no_execution,
            "stale_approval_rejected": stale_rejected,
            "passed": initial_usable
            and recovery["status"] == "recovered"
            and memory["status"] == "recovered"
            and memory_used
            and insufficient["status"] == "needs_evidence"
            and no_execution
            and stale_rejected is not False,
        }
        rows.append(row)
        report = {
            "created_at": now(),
            "model": settings.active_model,
            "provider": settings.provider,
            "tool_protocol": settings.ollama_tool_mode,
            "timeout_seconds": settings.timeout,
            "sequential": True,
            "expected_repetitions": 3,
            "complete": len(rows) == 3,
            "cases": rows,
            "passed": len(rows) == 3 and all(r["passed"] for r in rows),
        }
        (destination / "repeatability.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    asyncio.run(demonstrate())
