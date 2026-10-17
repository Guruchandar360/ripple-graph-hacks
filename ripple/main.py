import asyncio
import json
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ripple.agent import Agent
from ripple.config import Settings
from ripple.fixtures import SCENARIOS, initial_sources, new_state
from ripple.models import DomainError, EvidenceRequest, StartRun
from ripple.readiness import checklist
from ripple.repository import GraphRepository, projection
from ripple.service import RippleService

ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)


def create_app(repository=None, settings=None, agent_override=None) -> FastAPI:
    settings = settings or Settings()
    if os.getenv("WEB_CONCURRENCY", "1") != "1":
        raise RuntimeError("Ripple requires one worker for mutation and quota coordination.")
    repo = repository or GraphRepository(settings)
    service = RippleService(repo, settings)
    agent = agent_override or Agent(service, settings)
    tasks: set[asyncio.Task] = set()

    @asynccontextmanager
    async def lifespan(app):
        try:
            await asyncio.to_thread(repo.interrupt_previous)
        except DomainError:
            logger.warning("FalkorDB unavailable at startup; live operations will fail closed.")
        yield
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="Ripple", version="0.1.0", lifespan=lifespan)
    app.state.service, app.state.repo, app.state.agent = service, repo, agent

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=exc.status)

    @app.middleware("http")
    async def workspace_cookie(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            permitted = {
                f"{request.url.scheme}://{request.headers.get('host')}",
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            }
            if origin and origin not in permitted:
                return JSONResponse(
                    {"error": {"code": "invalid_origin", "message": "Cross-origin mutation rejected."}},
                    status_code=403,
                )
        cookie = request.cookies.get("ripple_workspace", "")
        workspace = cookie if re.fullmatch(r"[a-f0-9]{32}", cookie) else uuid.uuid4().hex
        request.state.workspace = workspace
        response = await call_next(request)
        if workspace != cookie:
            response.set_cookie(
                "ripple_workspace",
                workspace,
                httponly=True,
                secure=settings.cookie_secure,
                samesite="lax",
                max_age=7 * 86400,
            )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.get("/api/health")
    def health():
        try:
            repo.health()
            database = "connected"
        except DomainError:
            database = "unavailable"
        return {
            "database": database,
            "model": settings.active_model,
            "model_provider": settings.provider,
            "model_configured": settings.model_configured,
            "synthetic": True,
            "limits": {
                "workspace_daily": settings.workspace_daily_runs,
                "global_daily": settings.global_daily_runs,
            },
        }

    @app.get("/api/scenarios")
    def scenarios():
        return SCENARIOS

    @app.get("/api/preview/{scenario_id}")
    def preview(scenario_id: str):
        scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
        if not scenario:
            raise DomainError("Unknown scenario.", 404, "not_found")
        state = new_state()
        state["scenario"], state["sources"] = scenario, initial_sources(scenario_id)
        nodes, edges = projection(state)
        # Static fixture inspection is explicitly separate from live graph operations.
        return {
            "preview": True,
            "label": "Synthetic fixture preview — not a live investigation or replay",
            "scenario": scenario,
            "graph": {"nodes": nodes, "edges": edges},
        }

    @app.get("/api/workspace")
    def workspace(request: Request):
        return service.state(request.state.workspace)

    @app.post("/api/scenarios/{scenario_id}/load")
    def load_scenario(request: Request, scenario_id: str):
        return service.load(request.state.workspace, scenario_id)

    @app.post("/api/runs", status_code=202)
    async def start_run(request: Request, body: StartRun):
        run = await asyncio.to_thread(service.start, request.state.workspace, body.mode)
        task = asyncio.create_task(agent.run(request.state.workspace, run["id"]))
        tasks.add(task)
        task.add_done_callback(tasks.discard)
        return run

    @app.get("/api/runs/{run_id}")
    def get_run(request: Request, run_id: str, cursor: int = 0):
        return service.get_run(request.state.workspace, run_id, max(0, cursor))

    @app.post("/api/runs/{run_id}/evidence")
    def inject_evidence(request: Request, run_id: str, body: EvidenceRequest):
        return service.inject(request.state.workspace, run_id)

    @app.post("/api/runs/{run_id}/actions/{action_id}/execute")
    def execute_action(request: Request, run_id: str, action_id: str):
        return service.execute(request.state.workspace, run_id, action_id)

    @app.get("/api/graph")
    def graph(request: Request):
        with service.lock(request.state.workspace):
            return repo.graph(request.state.workspace)

    @app.get("/api/memory")
    def memory(request: Request):
        with service.lock(request.state.workspace):
            return repo.memories(request.state.workspace)

    @app.get("/api/evaluations")
    def evaluations():
        artifact = ROOT / "artifacts" / "evaluations.json"
        if not artifact.exists():
            artifact = ROOT / "demo" / "evaluations.json"
        if artifact.exists():
            return json.loads(artifact.read_text(encoding="utf-8"))
        return {
            "measured": False,
            "cases": [],
            "summary": None,
            "message": "No benchmark has been executed. No scores are claimed.",
        }

    @app.get("/api/readiness")
    def readiness():
        try:
            graph_connected = repo.health()
        except DomainError:
            graph_connected = False
        return checklist(ROOT, graph_connected=graph_connected, model_configured=settings.model_configured)

    @app.get("/api/demo-video")
    def demo_video():
        path = ROOT / "demo" / "ripple-demo.webm"
        if not path.is_file():
            raise DomainError("No demo video has been recorded.", 404, "not_found")
        return FileResponse(path, media_type="video/webm")

    @app.get("/api/replays")
    def replays():
        directory = ROOT / "artifacts" / "replays"
        if not directory.exists():
            directory = ROOT / "demo" / "replays"
        return (
            [
                {**json.loads(p.read_text(encoding="utf-8")), "id": p.stem, "replay": True}
                for p in sorted(directory.glob("*.json"))
            ]
            if directory.exists()
            else []
        )

    dist = ROOT / "frontend" / "dist"
    if (dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str):
        if path.startswith("api/"):
            raise DomainError("API endpoint not found.", 404, "not_found")
        if path == "favicon.svg" and (dist / path).exists():
            return FileResponse(dist / path)
        if (dist / "index.html").exists():
            return FileResponse(dist / "index.html")
        return JSONResponse(
            {"message": "Ripple API is running. Build frontend or use the Vite dev server.", "docs": "/docs"}
        )

    return app


app = create_app()
