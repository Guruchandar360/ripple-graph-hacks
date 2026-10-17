from dataclasses import replace

from fastapi.testclient import TestClient

from ripple.main import create_app


class IdleAgent:
    async def run(self, workspace, run_id):
        pass


def test_api_cookies_are_private_and_foreign_origins_cannot_mutate(repo, settings):
    app = create_app(repo, settings, IdleAgent())
    with TestClient(app) as client:
        result = client.get("/api/scenarios")
        assert result.status_code == 200
        assert "HttpOnly" in result.headers["set-cookie"]
        assert "SameSite=lax" in result.headers["set-cookie"]
        rejected = client.post("/api/scenarios/memory/load", headers={"Origin": "https://untrusted.example"})
        assert rejected.status_code == 403
        assert repo.states == {}


def test_api_isolates_two_visitors_and_uses_event_cursors(repo, settings):
    app = create_app(repo, settings, IdleAgent())
    with TestClient(app) as a, TestClient(app) as b:
        assert a.post("/api/scenarios/outdated-fix/load").status_code == 200
        created = a.post("/api/runs", json={"mode": "graph"})
        assert created.status_code == 202
        rid = created.json()["id"]
        assert a.get(f"/api/runs/{rid}?cursor=1").json()["events"] == []
        assert b.get(f"/api/runs/{rid}").status_code == 404
        assert b.get("/api/memory").json() == []


def test_preview_remains_available_but_live_graph_outage_is_explicit(repo, settings):
    repo.online = False
    with TestClient(create_app(repo, settings, IdleAgent())) as client:
        preview = client.get("/api/preview/outdated-fix")
        assert preview.status_code == 200
        assert preview.json()["preview"] is True
        assert "not a live investigation" in preview.json()["label"]
        for method, path in [("get", "/api/graph"), ("post", "/api/scenarios/outdated-fix/load")]:
            response = getattr(client, method)(path)
            assert response.status_code == 503
            assert response.json()["error"]["code"] == "graph_unavailable"


def test_missing_model_key_never_creates_a_live_run(repo, settings):
    settings = replace(settings, api_key="")
    with TestClient(create_app(repo, settings, IdleAgent())) as client:
        client.post("/api/scenarios/memory/load")
        response = client.post("/api/runs", json={"mode": "graph"})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "model_unconfigured"
        assert client.get("/api/workspace").json()["history"] == []


def test_request_validation_rejects_unknown_modes_and_evidence_events(repo, settings):
    with TestClient(create_app(repo, settings, IdleAgent())) as client:
        client.post("/api/scenarios/memory/load")
        assert client.post("/api/runs", json={"mode": "unbounded"}).status_code == 422
        assert client.post("/api/runs/fake/evidence", json={"event": "arbitrary"}).status_code == 422
