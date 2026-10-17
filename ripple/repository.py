"""FalkorDB persistence and graph tools. Production has no substitute store."""

import json
import logging
import re
from datetime import UTC, datetime

from falkordb import FalkorDB
from redis.backoff import NoBackoff
from redis.retry import Retry

from ripple.config import Settings
from ripple.fixtures import new_state
from ripple.models import DomainError, now

LABELS = {"Service", "Team", "Source", "Deployment", "Constraint", "Incident", "Action", "ProbeResult", "Run"}
RELATIONS = {
    "DEPENDS_ON",
    "OWNED_BY",
    "CHANGES",
    "SUPPORTED_BY",
    "BLOCKS",
    "AFFECTS",
    "PROPOSED",
    "EXECUTED",
    "VERIFIED_BY",
    "LEARNED_FROM",
}
logger = logging.getLogger(__name__)


def projection(state: dict) -> tuple[list[dict], list[dict]]:
    nodes, edges = [], []

    def add(sid, label, data):
        nodes.append({"id": sid, "label": label, "data": {**data, "id": sid}})

    def edge(a, b, kind, evidence="topology"):
        edges.append(
            {
                "id": f"{kind}:{a}:{b}",
                "source": a,
                "target": b,
                "kind": kind,
                "evidence_ids": [evidence] if evidence else [],
            }
        )

    for team in ["experience", "commerce", "platform"]:
        add(f"team-{team}", "Team", {"name": team.title()})
    for service in state["services"]:
        add(service["id"], "Service", service)
        edge(service["id"], f"team-{service['owner']}", "OWNED_BY")
    for a, b in state["dependencies"]:
        edge(a, b, "DEPENDS_ON")
    for source in state["sources"]:
        add(source["id"], "Source", source)
    if state["scenario"]:
        incident = state["scenario"]["incident"]
        add(incident, "Incident", {"name": incident, "summary": state["scenario"]["symptom"]})
        edge(incident, "checkout", "AFFECTS", "alert")
    if any(s["id"] == "deployment" for s in state["sources"]):
        add("deploy-v24", "Deployment", {"name": "Payments v2.4"})
        edge("deploy-v24", "payments", "CHANGES", "deployment")
        edge("deploy-v24", "deployment", "SUPPORTED_BY", "deployment")
    if any(s["id"] == "migration" and s["active"] for s in state["sources"]):
        add("schema-constraint", "Constraint", {"name": "v2.3 incompatible with schema 2"})
        edge("schema-constraint", "migration", "SUPPORTED_BY", "migration")
    for run in state["runs"].values():
        add(run["id"], "Run", {"name": run["id"], "status": run["status"], "created_at": run["created_at"]})
        for action in run.get("proposals", []):
            add(action["id"], "Action", action)
            edge(run["id"], action["id"], "EXECUTED" if action.get("result") else "PROPOSED", "")
            for sid in action["evidence_ids"]:
                if any(s["id"] == sid for s in state["sources"]):
                    edge(action["id"], sid, "SUPPORTED_BY", sid)
            if action["action"] == "rollback_deployment" and any(
                n["id"] == "schema-constraint" for n in nodes
            ):
                edge("schema-constraint", action["id"], "BLOCKS", "migration")
            for i, probe in enumerate((action.get("result") or {}).get("after", [])):
                pid = f"probe-{action['id']}-{i}"
                add(pid, "ProbeResult", probe)
                edge(action["id"], pid, "VERIFIED_BY", "")
    for memory in state["memory"]:
        mid = f"memory-{memory['id']}"
        add(mid, "Incident", memory)
        for run in state["runs"].values():
            if memory["id"] in run.get("memory_ids", []):
                edge(run["id"], mid, "LEARNED_FROM", "")
    return nodes, edges


class GraphRepository:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None

    def _query(self, graph: str, query: str, params: dict | None = None) -> list:
        try:
            if self.client is None:
                settings = self.settings
                self.client = FalkorDB(
                    host=settings.graph_host,
                    port=settings.graph_port,
                    username=settings.graph_username or None,
                    password=settings.graph_password or None,
                    ssl=settings.graph_ssl,
                    socket_connect_timeout=2,
                    socket_timeout=8,
                    ssl_check_hostname=True,
                    retry=Retry(NoBackoff(), 0),
                )
            return self.client.select_graph(graph).query(query, params or {}).result_set
        except Exception as exc:
            raise DomainError(
                "FalkorDB is unavailable. Check the server address, TLS, and credentials.",
                503,
                "graph_unavailable",
            ) from exc

    @staticmethod
    def graph_name(workspace: str) -> str:
        if not re.fullmatch(r"[a-f0-9]{32}", workspace):
            raise DomainError("Invalid workspace identifier.", 400, "invalid_workspace")
        return f"ripple_{workspace}"

    def health(self) -> bool:
        return bool(self._query("ripple_control", "RETURN 1"))

    def register(self, workspace: str):
        self.graph_name(workspace)
        rows = self._query(
            "ripple_control",
            """
        MERGE (c:Capacity {id:'visitors'}) ON CREATE SET c.count=0
        WITH c OPTIONAL MATCH (existing:Visitor {id:$workspace})
        WITH c, existing WHERE existing IS NOT NULL OR c.count < $limit
        MERGE (v:Visitor {id:$workspace})
        ON CREATE SET v.created_at=$now, c.count=c.count+1
        RETURN v.id
        """,
            {"workspace": workspace, "limit": self.settings.max_workspaces, "now": now()},
        )
        if not rows:
            raise DomainError(
                "Demo workspace capacity reached. Recorded walkthroughs remain available.",
                429,
                "workspace_capacity",
            )

    def read(self, workspace: str) -> dict:
        rows = self._query(self.graph_name(workspace), "MATCH (w:Workspace {id:'root'}) RETURN w.payload")
        return json.loads(rows[0][0]) if rows else new_state()

    def save(self, workspace: str, state: dict):
        # Snapshot, simulator transition, audit events and graph projection commit together.
        # CAS prevents a stale process from overwriting a newer version.
        expected = state["version"]
        updated = {**state, "version": expected + 1}
        nodes, edges = projection(updated)
        params = {"expected": expected, "version": expected + 1, "payload": json.dumps(updated)}
        query = """MERGE (w:Workspace {id:'root'}) ON CREATE SET w.version=0
        WITH w WHERE w.version=$expected
        OPTIONAL MATCH (e:Entity) DETACH DELETE e
        WITH DISTINCT w SET w.version=$version, w.payload=$payload
        """
        aliases = {}
        for i, node in enumerate(nodes):
            assert node["label"] in LABELS
            alias = f"n{i}"
            aliases[node["id"]] = alias
            params[f"id{i}"] = node["id"]
            params[f"data{i}"] = json.dumps(node["data"])
            query += f"CREATE ({alias}:Entity:{node['label']} {{id:$id{i}, data:$data{i}}})\n"
        for i, rel in enumerate(edges):
            assert rel["kind"] in RELATIONS
            params[f"edge{i}"] = json.dumps(rel)
            params[f"eid{i}"] = rel["id"]
            query += (
                f"CREATE ({aliases[rel['source']]})-[:{rel['kind']} "
                f"{{id:$eid{i}, data:$edge{i}}}]->({aliases[rel['target']]})\n"
            )
        rows = self._query(self.graph_name(workspace), query + "RETURN w.version", params)
        if not rows:
            raise DomainError("Workspace changed. Refresh and retry.", code="stale_write")
        state["version"] = expected + 1

    def graph(self, workspace: str) -> dict:
        name = self.graph_name(workspace)
        nodes = self._query(name, "MATCH (n:Entity) RETURN n.id, labels(n), n.data")
        edges = self._query(name, "MATCH (:Entity)-[r]->(:Entity) RETURN r.data")
        return {
            "nodes": [
                {"id": n[0], "label": next(x for x in n[1] if x != "Entity"), "data": json.loads(n[2])}
                for n in nodes
            ],
            "edges": [json.loads(r[0]) for r in edges],
        }

    def impact(self, workspace: str, target: str) -> dict:
        rows = self._query(
            self.graph_name(workspace),
            """
        MATCH p=(s:Service)-[:DEPENDS_ON*0..5]->(t:Service {id:$target})
        RETURN s.id, [n IN nodes(p) | n.id], [r IN relationships(p) | r.id]
        """,
            {"target": target},
        )
        return {
            "target": target,
            "affected_services": sorted({r[0] for r in rows}),
            "paths": [{"nodes": r[1], "edges": r[2]} for r in rows],
            "evidence_ids": ["topology"],
        }

    def context(self, workspace: str) -> dict:
        rows = self._query(
            self.graph_name(workspace),
            """
        MATCH (s:Service)-[:OWNED_BY]->(t:Team)
        RETURN s.id, t.data
        """,
        )
        sources = self.sources(workspace)
        return {
            "ownership": [{"service": r[0], "team": json.loads(r[1])} for r in rows],
            "sources": [s for s in sources if s.get("active")],
            "evidence_ids": [s["id"] for s in sources if s.get("active")],
        }

    def sources(self, workspace: str) -> list[dict]:
        return [
            json.loads(r[0])
            for r in self._query(self.graph_name(workspace), "MATCH (s:Source) RETURN s.data")
        ]

    def memories(self, workspace: str) -> list[dict]:
        # Prior verified/failed outcomes are graph incident nodes, independent of chat context.
        return [
            json.loads(r[0])
            for r in self._query(
                self.graph_name(workspace),
                "MATCH (i:Incident) WHERE i.id STARTS WITH 'memory-' RETURN i.data",
            )
        ]

    def reserve_run(self, workspace: str):
        day = datetime.now(UTC).date().isoformat()
        rows = self._query(
            "ripple_control",
            """
        MERGE (g:Usage {id:$global}) ON CREATE SET g.count=0
        MERGE (w:Usage {id:$local}) ON CREATE SET w.count=0
        WITH g,w WHERE g.count < $global_limit AND w.count < $local_limit
        SET g.count=g.count+1, w.count=w.count+1 RETURN g.count,w.count
        """,
            {
                "global": day,
                "local": f"{day}:{workspace}",
                "global_limit": self.settings.global_daily_runs,
                "local_limit": self.settings.workspace_daily_runs,
            },
        )
        if not rows:
            raise DomainError(
                "Today's free live-run quota is exhausted. Replay remains available.", 429, "quota_exhausted"
            )

    def interrupt_previous(self):
        rows = self._query("ripple_control", "MATCH (v:Visitor) RETURN v.id")
        for row in rows:
            state = self.read(row[0])
            changed = False
            for run in state["runs"].values():
                if run["status"] == "investigating":
                    run["status"] = "interrupted"
                    run["error"] = "Server restarted. Start a fresh investigation; no action was repeated."
                    changed = True
            if changed:
                self.save(row[0], state)
