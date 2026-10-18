# Verification — October 18, 2026 IST

## Automated implementation checks

- **46 backend tests passed** in [clean Linux CI](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39131703437), including **two real FalkorDB integration tests** against version 6.0.2.
- **Eight application browser tests passed**: fixture honesty, scenarios/navigation, responsive layout, keyboard-operated mobile drawer, command navigation, participant checklist and late startup responses preserving a selected replay.
- **One static-showcase browser test passed**, including its public subpath, replay labels, disabled live actions and absence of outgoing mutations.
- Strict TypeScript compilation, production build and Ruff checks passed.
- Locally: 44 backend tests passed; two real-server integration tests were skipped in that run. The browser preview suite uses its own disconnected server and empty credentials, independently of the developer's private `.env`.

Behavioral tests use an explicit test-only repository double. Agent-loop unit tests use a scripted function-call provider. These are distinct from the two native-database tests and the real-model measurements below.

The real database tests verify actual incoming dependency paths, persisted action results and memory, native policy supersession, and rejection of stale approval. The static showcase never substitutes for FalkorDB during live operations.

Browser coverage includes the desktop workspace at 1280×720, 1366×768,
1440×900, 1536×864 and 1920×1080 at normal zoom. The page scrolls naturally; the
graph is at least 420 pixels tall, while timeline and recommendation text expand
without internal clipping. Short windows down to 600 pixels high preserve bounded
evidence dialogs; phone/tablet navigation reaches every view.
`frontend/scripts/verify-public.mjs` checks the actual published site, natural
flow, browser errors and MP4 delivery. `frontend/scripts/audit-design.mjs` checks
the bundled fonts, a 12px minimum text size, graph labels and clipping across
desktop, tablet and phone sizes, and saves screenshots in `artifacts/`.

The decision column retains Decision, Change and Sources shortcuts so
lower evidence cards are discoverable without changing browser zoom. Each shortcut
scrolls to and focuses its destination. Keyboard users can navigate the mobile
drawer and operate graph controls. Browser checks exercise these interactions.

## Real model measurements

The complete evidence-first CPU rerun at `66eeedc` reached **23/24 expected
terminal states**: graph **12/12**, full-document baseline **11/12**. Graph mode
verified eight recoveries; baseline verified seven. Both reported valid citations
in all 12 cases and no executed policy violations. Graph impact was complete in
10/12 cases, baseline 11/12. Graph median elapsed was 206.0 seconds versus 94.0
seconds for baseline. These budgets are 300 seconds per conversation; they do
not establish behavior within the normal 120-second application limit. The raw
workflow and every replay are linked from [MEASUREMENTS.md](MEASUREMENTS.md).
This is a small development sample with known fixtures, not general superiority.
The earlier 22/24 report remains archived.

Development smoke tests are preserved under `demo/development/`:

- Qwen3 1.7B: both graph and baseline exhausted eight turns; 0/2 verified recoveries. The graph run's incompatible rollback proposal was blocked by the independent guard.
- Qwen3 4B: both workflows exceeded the configured 300-second CPU window; 0/2 recoveries.

These failures are not hidden or reclassified as successful tests. Subsequent model/prompt changes are separate measurements, not additional successes added to the same sample. Release evaluation and actual replay artifacts are published under `demo/` when complete. No Gemini performance is inferred from local-model runs, and development fixtures are not held-out test data.

## Delivery

The complete 24-run CPU comparison is published in [MEASUREMENTS.md](MEASUREMENTS.md)
with the raw report and all replay records. It does not establish graph superiority;
the current sample contains timeouts and incomplete impact reporting. Source versions
and separate development experiments are recorded in `demo/PROVENANCE.md`.

[Public source](https://github.com/Guruchandar360/ripple-graph-hacks) and [read-only showcase](https://guruchandar360.github.io/ripple-graph-hacks/) are available. The showcase serves synthetic fixtures and actual recorded output when exported; it has no live backend, graph connection or model credentials.

The full application is reproducible with the README's Docker/Cloud database and Gemini or explicitly selected Ollama configuration. CI performs clean package installation and uses real container services. Free Cloud and Render resources have been created; integrated cloud verification is pending. This workstation has no Docker/working WSL; a fresh local live setup is not claimed here.

The actual Google GenAI SDK completed a native `report_status` function call on
`gemini-3.8-flash` in 4.312 seconds. `gemini-2.5-flash` returned 404 for this
account. Sanitized reports are in `demo/provider-checks/`. The account's checked
quota is 5 requests/minute and 20/day. Provider access alone is not an integrated
agent result, and no performance is inferred from the CPU comparison.

## Participant-owned checks

WeMakeDevs registration is not verified; the inspected browser session is signed out. Team eligibility, personal technical understanding/contribution, final track selection and submission must be completed by the participant. The repository's checklist deliberately leaves these steps pending.

## Additional measured proof

The README's Docker Compose setup completed a model-backed recovery through real HTTP requests in 186.295 seconds with a five-turn CPU budget and a 300-second window. It verified all three affected request probes, returned the identical result for duplicate approval, preserved memory across both a scenario reload and a database container restart, and returned HTTP 404 to a different visitor. See [the actual workflow](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39033501898) and `demo/http-proof.json`. This used Ollama with the explicit JSON tool protocol, not Gemini. An earlier successful eight-turn proof and the later eight-turn timeout are both preserved under `demo/development/`.

A captioned replay video is committed as `demo/ripple-demo.mp4`, with the original WebM retained. The decoded recording is 81.68 seconds at 1440×1000. It shows one complete passing sequence in one workspace: stale approval rejected, recovery verified, the actual outcome loaded into a fresh conversation, and insufficient evidence causing no execution. Source IDs and configuration are in `demo/video.json`.

The previously retained combined configuration reached **22/24 expected terminal states** and **14 verified recoveries**, with zero executed policy violations. The graph workflow reached 10/12 expected states and the full-document baseline 12/12; this is not evidence of general graph superiority. Its three-sequence check passed **1/3**, so that measurement did not meet the three-consecutive-run gate. All three fresh conversations retrieved the actual earlier model outcome, but none explicitly cited it. Those reports measure `2c8aaaa`. The current evidence-first revision is being rerun separately, with stricter acceptance requiring both memory retrieval and citation. Failed and alternative measurements remain published.

The first complete 24-run development evaluation is preserved in `demo/development/first-full-suite.json`. It met 14 expected terminal states and recorded 13 verified recoveries, with substantial impact-reporting failures. Those observations led to current-context preloading, valid-service enums and policy-derived terminal tools. Later measurements are reported separately.
