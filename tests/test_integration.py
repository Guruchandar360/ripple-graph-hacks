"""Opt-in real FalkorDB tests. Never silently use a test double here."""

import os
import uuid
import warnings

import pytest

from ripple.config import Settings
from ripple.repository import GraphRepository
from ripple.service import RippleService

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("FALKORDB_INTEGRATION") != "1",
        reason="Set FALKORDB_INTEGRATION=1 with a real FalkorDB server",
    ),
]


def test_real_graph_round_trip_traversal_and_recovery():
    repository = GraphRepository(Settings())
    service = RippleService(repository, Settings(api_key="integration-no-model-call"))
    workspace = uuid.uuid4().hex
    try:
        service.load(workspace, "memory")
        assert repository.read(workspace)["scenario"]["id"] == "memory"
        impact = repository.impact(workspace, "payments")
        assert set(impact["affected_services"]) == {"storefront", "checkout", "payments"}
        assert any(p["nodes"] == ["storefront", "checkout", "payments"] for p in impact["paths"])
        assert len(repository.graph(workspace)["nodes"]) >= 6
        run = service.start(workspace)
        service.tool(workspace, run["id"], "get_context", {})
        probe = service.tool(workspace, run["id"], "probe_service", {"service": "payments"})
        proposal = service.tool(
            workspace,
            run["id"],
            "propose_action",
            {
                "action": "disable_feature_flag",
                "target": "payments",
                "summary": "Disable the documented incompatible validation flag.",
                "evidence_ids": ["flag-config", *probe["evidence_ids"]],
            },
        )
        assert service.execute(workspace, run["id"], proposal["action_id"])["verified"]
        assert repository.memories(workspace)[0]["verified"]
    finally:
        # Remove only the graph created by this test and its capacity registration.
        if repository.client:
            try:
                repository.client.select_graph(repository.graph_name(workspace)).delete()
                repository._query("ripple_control", "MATCH (v:Visitor {id:$id}) DELETE v", {"id": workspace})
                repository._query(
                    "ripple_control", "MATCH (c:Capacity {id:'visitors'}) SET c.count=c.count-1"
                )
            except Exception as exc:  # noqa: BLE001 -- preserve the original integration failure
                warnings.warn(f"Integration cleanup failed: {type(exc).__name__}", stacklevel=1)
