import threading
import uuid
from copy import deepcopy

from ripple import simulator
from ripple.config import Settings
from ripple.evidence import resolve_sources
from ripple.fixtures import SCENARIOS, initial_sources, migration_source, source
from ripple.models import Diagnosis, DomainError, Proposal, now
from ripple.repository import GraphRepository

ACTIVE = {"investigating"}


class RippleService:
    def __init__(self, repository: GraphRepository, settings: Settings):
        self.repo, self.settings = repository, settings
        self.locks: dict[str, threading.RLock] = {}
        self.lock_guard = threading.Lock()
        self.quota_lock = threading.Lock()

    def lock(self, workspace: str):
        with self.lock_guard:
            return self.locks.setdefault(workspace, threading.RLock())

    @staticmethod
    def event(run: dict, kind: str, title: str, detail: str, evidence_ids=None, **extra):
        run["events"].append(
            {
                "id": len(run["events"]) + 1,
                "kind": kind,
                "title": title,
                "detail": detail,
                "evidence_ids": evidence_ids or [],
                "at": now(),
                **extra,
            }
        )

    def load(self, workspace: str, scenario_id: str) -> dict:
        scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
        if not scenario:
            raise DomainError("Unknown scenario.", 404, "not_found")
        with self.lock(workspace):
            self.repo.register(workspace)
            state = self.repo.read(workspace)
            previous_graph = self.repo.graph(workspace) if state["scenario"] else None
            for run in state["runs"].values():
                if run["status"] in ACTIVE or run["status"] == "awaiting_approval":
                    if previous_graph:
                        run["graph_snapshot"] = previous_graph
                    run["status"] = "interrupted"
                    for p in run["proposals"]:
                        if not p.get("result"):
                            p["stale"] = True
                    self.event(run, "warning", "Scenario replaced", "Outstanding approval was invalidated.")
            state.update(
                scenario=deepcopy(scenario),
                generation=uuid.uuid4().hex,
                sources=initial_sources(scenario_id),
                simulator=simulator.seed(scenario_id),
                revision=state["revision"] + 1,
            )
            self.repo.save(workspace, state)
            return self.public_state(state)

    def archive_graph(self, workspace: str, state: dict, run: dict):
        # Preserve an actual queried projection for history/replay; never rebuild historical paths in the UI.
        if run["status"] != "investigating" and run["generation"] == state["generation"]:
            run["graph_snapshot"] = self.repo.graph(workspace)
            self.repo.save(workspace, state)

    @staticmethod
    def public_state(state: dict) -> dict:
        return {
            "scenario": state["scenario"],
            "revision": state["revision"],
            "history": [
                {
                    "id": r["id"],
                    "status": r["status"],
                    "incident": r["incident"],
                    "created_at": r["created_at"],
                    "mode": r["mode"],
                }
                for r in reversed(list(state["runs"].values()))
            ],
            "memory_count": len(state["memory"]),
        }

    def state(self, workspace: str):
        with self.lock(workspace):
            return self.public_state(self.repo.read(workspace))

    def start(self, workspace: str, mode="graph") -> dict:
        if not self.settings.model_configured:
            raise DomainError(
                "Set GEMINI_API_KEY in the server environment to start a live investigation.",
                503,
                "model_unconfigured",
            )
        with self.lock(workspace):
            state = self.repo.read(workspace)
            if not state["scenario"]:
                raise DomainError("Load a scenario first.", 400, "scenario_required")
            if any(r["status"] in ACTIVE for r in state["runs"].values()):
                raise DomainError("An investigation is already running in this workspace.")
            if len(state["runs"]) >= 40:
                raise DomainError(
                    "Workspace history is full. Use existing runs or a new workspace.", 429, "history_limit"
                )
            with self.quota_lock:
                self.repo.reserve_run(workspace)
            # New conversation: only persisted graph knowledge can supply prior outcomes.
            run = {
                "id": uuid.uuid4().hex,
                "incident": state["scenario"]["incident"],
                "generation": state["generation"],
                "revision": state["revision"],
                "mode": mode,
                "model_provider": self.settings.provider,
                "model": self.settings.active_model,
                "tool_protocol": self.settings.ollama_tool_mode
                if self.settings.provider == "ollama"
                else "native",
                "status": "investigating",
                "created_at": now(),
                "events": [],
                "proposals": [],
                "seen_evidence": [],
                "memory_ids": [],
                "diagnosis": None,
                "model_calls": 0,
                "elapsed_ms": 0,
                "error": None,
                "replay": False,
            }
            self.event(run, "observation", "Investigation opened", state["scenario"]["symptom"], ["alert"])
            run["seen_evidence"].append("alert")
            previous = next(
                (r for r in reversed(list(state["runs"].values())) if r["generation"] == state["generation"]),
                None,
            )
            changed = (
                next((e for e in reversed(previous["events"]) if e["title"] == "Evidence changed"), None)
                if previous
                else None
            )
            if changed:
                run["revalidates_run_id"] = previous["id"]
                if previous["proposals"]:
                    old = previous["proposals"][-1]
                    run["previous_recommendation"] = {
                        "action": old["action"],
                        "target": old["target"],
                        "revision": old["revision"],
                    }
                self.event(
                    run,
                    "observation",
                    "Evidence revision revalidation",
                    "A fresh conversation is checking the changed evidence. The prior recommendation remains inspectable in incident history.",
                    changed["evidence_ids"],
                    revalidates_run_id=previous["id"],
                )
            state["runs"][run["id"]] = run
            self.repo.save(workspace, state)
            return deepcopy(run)

    def get_run(self, workspace: str, run_id: str, cursor=0) -> dict:
        with self.lock(workspace):
            state = self.repo.read(workspace)
            run = self._run(state, run_id)
            result = deepcopy(run)
            result["cursor"] = len(run["events"])
            result["events"] = [e for e in run["events"] if e["id"] > cursor]
            result["current_revision"] = state["revision"]
            return result

    @staticmethod
    def _run(state: dict, run_id: str) -> dict:
        if run_id not in state["runs"]:
            raise DomainError("Run not found in this workspace.", 404, "not_found")
        return state["runs"][run_id]

    @staticmethod
    def _current(state: dict, run: dict):
        if state["generation"] != run["generation"]:
            raise DomainError("Scenario changed. Start a new investigation.", code="stale_run")

    @staticmethod
    def _citations(state: dict, run: dict, citations: list[str]):
        active = {s["id"] for s in state["sources"] if s["active"]}
        active.update(f"memory-{m['id']}" for m in state["memory"])
        if not set(citations).issubset(active & set(run["seen_evidence"])):
            raise DomainError(
                "Citations must identify active evidence actually retrieved in this run.",
                400,
                "invalid_citation",
            )

    def tool(self, workspace: str, run_id: str, name: str, args: dict, *, origin="model") -> dict:
        with self.lock(workspace):
            state = self.repo.read(workspace)
            run = self._run(state, run_id)
            self._current(state, run)
            if run["status"] != "investigating":
                raise DomainError("This run is no longer investigating.", code="run_finished")
            if name == "get_impact":
                if run["mode"] == "baseline":
                    raise DomainError("Graph traversal is disabled for the document baseline.", 400)
                target = args.get("service", "payments")
                self._service(state, target)
                result = self.repo.impact(workspace, target)
                self.event(
                    run,
                    "observation",
                    "Dependency paths retrieved",
                    f"Followed incoming dependency paths for {target}.",
                    ["topology"],
                    paths=result["paths"],
                )
            elif name == "get_context":
                if run["mode"] == "baseline":
                    result = {
                        "sources": self.repo.sources(workspace),
                        "evidence_ids": [s["id"] for s in state["sources"] if s["active"]],
                    }
                    result["sources"] = [s for s in result["sources"] if s["active"]]
                else:
                    result = self.repo.context(workspace)
                self.event(
                    run,
                    "observation",
                    "Investigation context loaded"
                    if origin == "application_preflight"
                    else "Current evidence retrieved",
                    "Application preflight loaded current source records before the first model call."
                    if origin == "application_preflight"
                    else "Read source records, ownership and deployment context.",
                    result["evidence_ids"],
                    origin=origin,
                )
            elif name == "retrieve_memory":
                if run["mode"] == "baseline":
                    raise DomainError("Graph incident-memory retrieval is disabled for this baseline.", 400)
                target = args.get("service", "payments")
                self._service(state, target)
                memories = self.repo.memories(workspace, target)
                result = {"outcomes": memories, "evidence_ids": [m["id"] for m in memories]}
                run["memory_ids"] = [m["id"].removeprefix("memory-") for m in memories]
                self.event(
                    run,
                    "observation",
                    "Incident memory retrieved",
                    f"Found {len(memories)} persisted outcomes. Recheck applicability before reuse.",
                    result["evidence_ids"],
                )
            elif name == "inspect_source":
                sid = args.get("source_id")
                record = next((s for s in state["sources"] if s["id"] == sid and s["active"]), None)
                if not record:
                    raise DomainError("Active source not found.", 404, "not_found")
                result = {"source": record, "evidence_ids": [sid]}
                self.event(run, "observation", "Source inspected", record["title"], [sid])
            elif name == "probe_service":
                target = args.get("service", "checkout")
                self._service(state, target)
                observation = simulator.probe(state["simulator"], target, state["dependencies"])
                sid = f"probe-{uuid.uuid4().hex[:12]}"
                record = source(
                    sid, f"Synthetic probe · {target}", observation["detail"], now(), **observation
                )
                state["sources"].append(record)
                result = {"probe": observation, "evidence_ids": [sid]}
                self.event(
                    run, "observation", f"{target.title()} probe completed", observation["detail"], [sid]
                )
            elif name == "submit_diagnosis":
                diagnosis = Diagnosis.model_validate(args)
                self._citations(state, run, diagnosis.evidence_ids)
                for target in diagnosis.affected_services:
                    self._service(state, target)
                run["diagnosis"] = diagnosis.model_dump()
                run["status"] = "needs_evidence" if diagnosis.missing_evidence else "complete"
                self.event(
                    run, "hypothesis", "Investigation assessment", diagnosis.summary, diagnosis.evidence_ids
                )
                result = {"accepted": True, "status": run["status"]}
            elif name == "propose_action":
                proposal = Proposal.model_validate(args)
                self._citations(state, run, proposal.evidence_ids)
                if not any(
                    s["id"] in run["seen_evidence"]
                    and s["id"].startswith("probe-")
                    and s["active"]
                    and s.get("service") == proposal.target
                    for s in state["sources"]
                ):
                    raise DomainError("Probe the target before proposing an action.", 400, "probe_required")
                p = {
                    **proposal.model_dump(),
                    "id": uuid.uuid4().hex,
                    "revision": state["revision"],
                    "generation": state["generation"],
                    "stale": False,
                    "result": None,
                    "created_at": now(),
                }
                blocked = self.block_reason(workspace, state, p)
                p["blocked_reason"] = blocked
                run["proposals"].append(p)
                self.event(
                    run,
                    "warning" if blocked else "hypothesis",
                    "Action blocked" if blocked else "Recovery proposed",
                    blocked or proposal.summary,
                    proposal.evidence_ids,
                    action_id=p["id"],
                )
                if not blocked:
                    run["status"] = "awaiting_approval"
                result = {"accepted": not bool(blocked), "action_id": p["id"], "blocked_reason": blocked}
            else:
                raise DomainError("Tool is not allowlisted.", 400, "invalid_tool")
            run["seen_evidence"] = sorted(set(run["seen_evidence"]) | set(result.get("evidence_ids", [])))
            self.repo.save(workspace, state)
            self.archive_graph(workspace, state, run)
            return result

    def record_tool_error(self, workspace: str, run_id: str, name: str, detail: str):
        with self.lock(workspace):
            state = self.repo.read(workspace)
            run = self._run(state, run_id)
            self.event(run, "warning", "Tool request rejected", f"{name}: {detail[:700]}")
            self.repo.save(workspace, state)

    @staticmethod
    def _service(state: dict, target: str):
        if target not in {s["id"] for s in state["services"]}:
            raise DomainError("Unknown simulator service.", 400, "invalid_service")

    def block_reason(self, workspace: str, state: dict, action: dict) -> str | None:
        sources = {s["id"]: s for s in state["sources"] if s["active"]}
        rules = self.repo.policies(workspace, action["action"], action["target"])
        blocked = [rule for rule in rules if not rule["allowed"]]
        if blocked:
            return " ".join(rule["reason"] for rule in blocked)
        if action["action"] == "rollback_deployment" and not any(rule["allowed"] for rule in rules):
            return "Current ledger compatibility is unverified. Obtain migration evidence before rollback."
        if action["action"] == "disable_feature_flag" and (
            action["target"] != "payments" or not any(s.get("flag_enabled") is True for s in sources.values())
        ):
            return "No applicable feature-flag evidence exists for this target."
        if action["action"] == "restart_service" and not any(
            "probe-" in sid for sid in action["evidence_ids"]
        ):
            return "A restart needs current target probe evidence."
        return None

    def inject(self, workspace: str, run_id: str) -> dict:
        with self.lock(workspace):
            state = self.repo.read(workspace)
            run = self._run(state, run_id)
            self._current(state, run)
            if state["scenario"]["id"] != "outdated-fix":
                raise DomainError("This scenario has no migration evidence event.", 400)
            if any(s["id"] == "migration" for s in state["sources"]):
                raise DomainError("Migration evidence has already been ingested.")
            if run["status"] == "investigating":
                raise DomainError("Wait for the investigation to pause before injecting evidence.")
            state["sources"] = resolve_sources([*state["sources"], migration_source()])
            state["revision"] += 1
            for candidate in state["runs"].values():
                if candidate["generation"] == state["generation"]:
                    for p in candidate["proposals"]:
                        if not p.get("result"):
                            p["stale"] = True
                    if candidate["status"] == "awaiting_approval":
                        candidate["status"] = "evidence_changed"
            self.event(
                run,
                "warning",
                "Evidence changed",
                "Ledger schema 2 is active. Earlier approvals are invalid. "
                "Run a fresh investigation against the new evidence.",
                ["migration"],
            )
            self.repo.save(workspace, state)
            self.archive_graph(workspace, state, run)
            return self.get_run(workspace, run_id)

    def execute(self, workspace: str, run_id: str, action_id: str) -> dict:
        with self.lock(workspace):
            state = self.repo.read(workspace)
            run = self._run(state, run_id)
            action = next((p for p in run["proposals"] if p["id"] == action_id), None)
            if not action:
                raise DomainError("Action not found in this run.", 404, "not_found")
            if action.get("result"):
                return deepcopy(action["result"])
            self._current(state, run)
            if action["stale"] or action["revision"] != state["revision"]:
                raise DomainError(
                    "Evidence changed. This approval is stale; investigate again.", code="stale_action"
                )
            reason = self.block_reason(workspace, state, action)
            if reason or action["blocked_reason"]:
                raise DomainError(reason or action["blocked_reason"], code="action_blocked")
            if run["status"] != "awaiting_approval":
                raise DomainError("This run is not awaiting action approval.", code="action_blocked")
            # A pure state transition followed by a single CAS graph commit makes execution retry-safe.
            # Verify the incident's user-facing path as well as the chosen action's blast radius.
            # A healthy but unrelated target must never manufacture a successful recovery.
            targets = sorted(
                set(self.repo.impact(workspace, action["target"])["affected_services"])
                | set(self.repo.impact(workspace, "checkout")["affected_services"])
            )
            before = [simulator.probe(state["simulator"], s, state["dependencies"]) for s in targets]
            try:
                runtime = simulator.execute(state["simulator"], action["action"], action["target"])
            except DomainError as exc:
                action["blocked_reason"] = exc.message
                run["status"] = "needs_evidence"
                self.event(
                    run,
                    "warning",
                    "Runtime precondition blocked execution",
                    exc.message,
                    action["evidence_ids"],
                    action_id=action_id,
                )
                self.repo.save(workspace, state)
                self.archive_graph(workspace, state, run)
                raise
            after = [simulator.probe(runtime, s, state["dependencies"]) for s in targets]
            verified = (
                bool(after) and any(not p["healthy"] for p in before) and all(p["healthy"] for p in after)
            )
            result = {
                "action_id": action_id,
                "verified": verified,
                "before": before,
                "after": after,
                "executed_at": now(),
                "synthetic": True,
            }
            action["result"] = result
            state["simulator"] = runtime
            state["revision"] += 1
            for old in state["sources"]:
                if old.get("record_type") in {"flag_config", "runtime_config"} or old["id"].startswith(
                    "probe-"
                ):
                    old["active"] = False
                    old["superseded_by"] = f"after-{action_id}"
            state["sources"].append(
                source(
                    f"after-{action_id}",
                    "Simulator action receipt",
                    f"Executed {action['action']} on {action['target']}. "
                    f"Current payments deployment: {runtime['deployment']}. "
                    f"strict_currency_validation={str(runtime['strict_currency_validation']).lower()}. "
                    f"Recovery verified by request probes: {verified}.",
                    now(),
                    record_type="runtime_config",
                    flag_enabled=runtime["strict_currency_validation"],
                )
            )
            run["status"] = "recovered" if verified else "recovery_failed"
            state["memory"].append(
                {
                    "id": action_id,
                    "incident": run["incident"],
                    "action": action["action"],
                    "target": action["target"],
                    "verified": verified,
                    "summary": action["summary"],
                    "result": result,
                    "applicability": "Recheck current deployment, ledger schema, flag and target probes.",
                    "created_at": now(),
                }
            )
            self.event(
                run,
                "verified" if verified else "warning",
                "Recovery verified" if verified else "Recovery not verified",
                "All affected synthetic probes passed."
                if verified
                else "The action ran, but affected services are still unhealthy.",
                action["evidence_ids"],
                action_id=action_id,
            )
            self.repo.save(workspace, state)
            self.archive_graph(workspace, state, run)
            return result

    def record_progress(self, workspace, run_id, *, calls=None, elapsed_ms=None, error=None):
        with self.lock(workspace):
            state = self.repo.read(workspace)
            run = self._run(state, run_id)
            if calls is not None:
                run["model_calls"] = calls
            if elapsed_ms is not None:
                run["elapsed_ms"] = elapsed_ms
            if error and run["status"] == "investigating":
                run["status"], run["error"] = "interrupted", error
                self.event(run, "warning", "Investigation paused", error)
            self.repo.save(workspace, state)
            self.archive_graph(workspace, state, run)
