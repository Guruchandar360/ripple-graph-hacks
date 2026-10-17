# Ripple

**Yesterday's fix can break today's system. Follow the evidence before acting.**

Ripple is a graph-backed incident investigator for a clearly labeled synthetic
commerce company. It traverses dependencies in FalkorDB, retrieves timestamped
sources and incident memory, proposes a recovery action, and verifies the result
against an executable Python simulator. Nothing touches production infrastructure.

## Current state

Implemented: React console, six-service graph fixture, three incident scenarios,
bounded Gemini function-calling loop, graph persistence, evidence revision checks,
idempotent simulator execution, incident memory, evaluation runner, and automated tests.

**Real Gemini/FalkorDB credentials are required for live investigation.** Without
them, the application offers a clearly labeled, read-only fixture preview and
connection diagnostics. This is not a simulated live agent or a fallback graph.
There are no claimed benchmark scores or recorded agent demos until actual runs
are executed and exported. Deployment and a public source URL require your accounts.

## Run locally

Requirements: Python 3.12+, Node 22+, a FalkorDB server (Cloud or Docker), and a
Gemini API key with access to the configured model. No paid fallback is enabled.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with your server-side credentials. Never put keys in frontend variables.
npm --prefix frontend ci
npm --prefix frontend run build
.\.venv\Scripts\python -m uvicorn ripple.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Open <http://127.0.0.1:8000>. The API reference is at <http://127.0.0.1:8000/docs>.
The fixture preview works without a graph/model connection. Health checks report
API-key presence, not successful model authorization; the first live run verifies it.

### macOS / Linux

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python -m uvicorn ripple.main:app --host 127.0.0.1 --port 8000 --workers 1
```

### FalkorDB

For Cloud, set host, port, username if required, password and `FALKORDB_SSL=true`
in `.env`. Obtain connection details from your own instance. For local Docker:

```sh
docker compose up -d
```

The graph server binds to localhost:6379, its Browser to localhost:3000. A named
volume and append-only persistence preserve data. Keep `FALKORDB_SSL=false` for
this localhost-only configuration. The image currently uses `latest`; pin a
tested release/digest for a reproducible hosted environment.

### Frontend development

Run the Python backend on port 8000. In another terminal:

```sh
npm --prefix frontend run dev
```

Visit <http://127.0.0.1:5173>. Vite proxies `/api` to FastAPI. Build again before
viewing changes through the production server on port 8000.

## Demo flow

1. Load **Yesterday's fix** and start a graph-backed investigation.
2. Inspect the dependency paths and cited sources. A rollback without verified
   compatibility is blocked; the agent may already choose the documented flag fix.
3. Once investigation pauses, inject the migration record. Pending approvals
   become stale. Inspect the amber **Evidence changed** event and source.
4. Start a fresh investigation. Approve a justified action; inspect actual
   before/after synthetic probes. Recovery is only claimed when all affected probes pass.
5. Load **A familiar failure**. This resets simulator state, not incident memory.
   A fresh model conversation can retrieve the prior measured outcome.
6. Load **Know what you don't know**. Missing origin telemetry should produce a
   request for evidence, not an executed remediation.

The exact model investigation is not scripted and may differ between runs. There
is no hidden instruction to select a scenario's expected action. Deterministic
guards are separate from model reasoning and are visible in the event log.

## Architecture

```mermaid
flowchart LR
  UI[React console] --> API[FastAPI / workspace cookie]
  API --> Agent[Bounded Gemini tool loop]
  Agent --> Tools[Parameterized graph tools]
  Tools --> Graph[(FalkorDB)]
  API --> Guard[Revision and compatibility guard]
  Guard --> Sim[Executable Python simulator]
  Sim --> Probes[Request health probes]
  Probes --> Graph
```

FalkorDB is required for graph queries, run history, quotas, evidence, simulator
state and memory. Each workspace has its own graph. Simulator state is never
returned wholesale to the agent; it sees only evidence and requested probes.
Graph paths show dependency impact, not proof of root cause.

Snapshots and their labeled node/edge projections are committed in one Cypher
mutation with optimistic version checks. Simulator actions are pure transitions
followed by this commit, so a retry cannot double-execute an action. One worker
serializes workspace mutations; **do not run multiple server workers or replicas**.
This is a small hackathon implementation: rebuilding the projection on each
mutation is intentionally simple, not a large-graph scaling strategy.

See [graph model and essential Cypher](docs/GRAPH.md), [evaluation methodology](docs/EVALUATION.md),
and [demo outline](docs/DEMO.md). See `/docs` for API request/response schemas.

## Verification

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check ripple tests
npm --prefix frontend run build
```

The default backend suite uses an explicit **test-only repository double** for
behavioral tests; the application and evaluator cannot use it. Real integration:

```powershell
$env:FALKORDB_INTEGRATION = '1'
.\.venv\Scripts\python -m pytest tests/test_integration.py -q
```

This test requires a real server, creates a unique workspace, performs actual
Cypher traversals and recovery commits, and removes its own graph afterward.
CI is configured to run this test with a FalkorDB service container.

For browser tests, use the disconnected/default configuration and a built frontend:

```powershell
Set-Location frontend
npx playwright install chromium
npm run test:e2e
```

The browser suite checks honest preview, evidence search, missing-key diagnostics,
navigation, and responsive layout. It does not claim to test live Gemini access.

## Evaluate actual model behavior

```powershell
.\.venv\Scripts\python -m ripple.evaluate --cases 1 --mode both
```

Run all 12 cases with `--cases 12`. This uses real model calls, graph storage,
and simulator actions. Full runs exceed the public demo's default ten-run daily
limit. Explicitly raise local `GLOBAL_DAILY_RUNS`, `WORKSPACE_DAILY_RUNS` and
`MAX_WORKSPACES` if account quotas permit; this does not increase Gemini's quota.
The runner stops on setup/quota failures rather than inventing results.

Results and actual replays go into `artifacts/`. The UI reads these files. These
files are ignored by Git; explicitly include desired synthetic result artifacts
in a release/deployment if you want visitors to inspect them. The model/API keys
and raw simulator fault configuration are not exported in replay artifacts.

## Free deployment

`render.yaml` defines one free Python web service that builds and serves the
frontend. Configure the required secrets in Render, plus a free FalkorDB instance
if available. `COOKIE_SECURE=true` is required on the HTTPS deployment. The daily
live-run and workspace limits bound the public demo; they are not billing controls.

Render's free instance can sleep. A new visitor may see a cold start before the
app loads. All live state is in FalkorDB, not Render's ephemeral filesystem.
Restarted investigations are marked interrupted on startup; actions are never
automatically repeated. No live deployment is claimed by the source configuration.

Public visitors can create up to 30 persisted workspaces by default. This is a
capacity cap, not an automatic retention policy; increase it deliberately or
clean up your own expired demonstration workspaces through FalkorDB Browser.

## Hackathon submission

Primary: **Agents That Act on Connected Data**. Also relevant: Company Brain
and Agent Memory and Coordination through provenance, ownership and memory.

Provide a public repository URL, live deployment or complete local instructions,
working demo video, graph model, actual Cypher, and measured results. Every fixture
is synthetic. The participant must review and understand the code, architecture,
queries and technical decisions before submitting.

**AI assistance disclosure:** Codex generated and revised implementation code,
tests, styling, and documentation with AI assistance. Automated tests cover selected
behaviors; actual provider/database integration and benchmark results must be
verified in the configured environment. Record your own review and contributions
in the final submission rather than claiming work or checks you did not perform.
