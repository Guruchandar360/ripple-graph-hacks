# Verification status — October 16, 2026

## Executed locally

- Backend: **30 passed, 1 skipped**. The skipped test requires a real FalkorDB server.
- Browser: **3 passed** against the built application in disconnected fixture-preview mode.
- TypeScript strict checks and Vite production build: passed.
- Ruff lint checks and Python compilation: passed.
- Python dependency consistency (`pip check`): passed.
- Inspected desktop and mobile screenshots; checked responsive overflow, mobile
  scenario selection, evidence search, dialogs, navigation, and browser errors.
- Confirmed `.env`, virtual environment, dependencies, and generated build files
  are ignored by Git.

Behavioral tests use an explicit test-only repository double. Agent-loop tests
use a scripted native-function-call provider. These validate orchestration and
guards; they are not evidence that an actual Gemini model successfully investigated
an incident or that real FalkorDB accepted every query.

## External verification still required

- Real FalkorDB integration test with configured connection credentials.
- Actual Gemini model availability, authorization, and free quota.
- Actual 12-case graph/baseline evaluations and replay exports.
- Three consecutive complete live demonstrations and video recording.
- Render deployment and public repository URL.

No live model scores, public deployment, or working-agent recording are claimed.
The evaluator exits before generating results when credentials are missing.
The app's preview is explicitly synthetic fixture inspection, not a live run.

## Artifacts

Local screenshots are in `artifacts/ripple-desktop.png` and
`artifacts/ripple-mobile.png`. The running local preview is at
http://127.0.0.1:8000. See the README for reproducible setup and commands.
