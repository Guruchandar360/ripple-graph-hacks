"""Explicit test double; never imported by the application or evaluation runner."""

from copy import deepcopy

import pytest

from ripple.config import Settings
from ripple.fixtures import new_state
from ripple.models import DomainError
from ripple.repository import projection
from ripple.service import RippleService


class TestRepository:
    __test__ = False

    def __init__(self):
        self.states = {}
        self.usage = {}
        self.online = True

    def check(self):
        if not self.online:
            raise DomainError("Test graph is offline", 503, "graph_unavailable")

    def health(self):
        self.check()
        return True

    def register(self, workspace):
        self.check()

    def read(self, workspace):
        self.check()
        return deepcopy(self.states.get(workspace, new_state()))

    def save(self, workspace, state):
        self.check()
        old = self.states.get(workspace, {"version": 0})
        if state["version"] != old["version"]:
            raise DomainError("Stale write", code="stale_write")
        state["version"] += 1
        self.states[workspace] = deepcopy(state)

    def graph(self, workspace):
        nodes, edges = projection(self.read(workspace))
        return {"nodes": nodes, "edges": edges}

    def impact(self, workspace, target):
        state = self.read(workspace)
        paths = []

        def walk(current, nodes):
            paths.append(
                {
                    "nodes": list(reversed(nodes)),
                    "edges": [
                        f"DEPENDS_ON:{a}:{b}"
                        for a, b in zip(list(reversed(nodes))[:-1], list(reversed(nodes))[1:])
                    ],
                }
            )
            for caller, dependency in state["dependencies"]:
                if dependency == current and caller not in nodes:
                    walk(caller, nodes + [caller])

        walk(target, [target])
        return {
            "target": target,
            "affected_services": sorted(p["nodes"][0] for p in paths),
            "paths": paths,
            "evidence_ids": ["topology"],
        }

    def sources(self, workspace):
        return self.read(workspace)["sources"]

    def context(self, workspace):
        sources = [s for s in self.sources(workspace) if s["active"]]
        return {"sources": sources, "evidence_ids": [s["id"] for s in sources]}

    def memories(self, workspace):
        return [{**m, "id": f"memory-{m['id']}"} for m in self.read(workspace)["memory"]]

    def reserve_run(self, workspace):
        self.check()
        self.usage[workspace] = self.usage.get(workspace, 0) + 1

    def interrupt_previous(self):
        pass


@pytest.fixture
def repo():
    return TestRepository()


@pytest.fixture
def settings():
    return Settings(api_key="test-key-not-a-real-key")


@pytest.fixture
def service(repo, settings):
    return RippleService(repo, settings)
