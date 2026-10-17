# Verification — October 17, 2026 IST

## Automated implementation checks

- **43 backend tests passed** in [clean Linux CI](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39025198861), including **two real FalkorDB integration tests** against version 6.0.2.
- **Six application browser tests passed**: fixture honesty, scenarios/navigation, responsive layout, command navigation and participant checklist.
- **One static-showcase browser test passed**, including its public subpath, replay labels, disabled live actions and absence of outgoing mutations.
- Strict TypeScript compilation, production build and Ruff checks passed.
- Locally: 41 backend tests passed; two real-server integration tests are skipped because this Windows host has no running FalkorDB server.

Behavioral tests use an explicit test-only repository double. Agent-loop unit tests use a scripted function-call provider. These are distinct from the two native-database tests and the real-model measurements below.

The real database tests verify actual incoming dependency paths, persisted action results and memory, native policy supersession, and rejection of stale approval. The static showcase never substitutes for FalkorDB during live operations.

## Real model measurements

Development smoke tests are preserved under `demo/development/`:

- Qwen3 1.7B: both graph and baseline exhausted eight turns; 0/2 verified recoveries. The graph run's incompatible rollback proposal was blocked by the independent guard.
- Qwen3 4B: both workflows exceeded the configured 300-second CPU window; 0/2 recoveries.

These failures are not hidden or reclassified as successful tests. Subsequent model/prompt changes are separate measurements, not additional successes added to the same sample. Release evaluation and actual replay artifacts are published under `demo/` when complete. No Gemini performance is inferred from local-model runs, and development fixtures are not held-out test data.

## Delivery

[Public source](https://github.com/Guruchandar360/ripple-graph-hacks) and [read-only showcase](https://guruchandar360.github.io/ripple-graph-hacks/) are available. The showcase serves synthetic fixtures and actual recorded output when exported; it has no live backend, graph connection or model credentials.

The full application is reproducible with the README's Docker/Cloud database and Gemini or explicitly selected Ollama configuration. CI performs clean package installation and uses real container services. A hosted live backend still needs the participant's Render/FalkorDB account configuration. This workstation has no Docker/working WSL; a fresh local live setup is not claimed here.

## Participant-owned checks

WeMakeDevs registration is not verified; the inspected browser session is signed out. Team eligibility, personal technical understanding/contribution, final track selection and submission must be completed by the participant. The repository's checklist deliberately leaves these steps pending.

## Additional measured proof

The real HTTP workflow completed a model-backed recovery in 94.462 seconds, verified all three affected request probes, returned the identical result for duplicate approval, preserved memory across a scenario reload, and returned HTTP 404 to a different visitor. See [the actual workflow](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39024504962) and `demo/http-proof.json`. This used Ollama with the explicit JSON tool protocol, not Gemini.

A captioned replay video is committed as `demo/ripple-demo.mp4`, with the original WebM retained. Chromium decoded the recording at 1440×1000; the initial smoke recording is 59.24 seconds. It is recorded actual agent output, not a hosted live agent.

The first complete 24-run development evaluation is preserved in `demo/development/first-full-suite.json`. It met 14 expected terminal states and recorded 13 verified recoveries, with substantial impact-reporting failures. Those observations led to current-context preloading, valid-service enums and policy-derived terminal tools. Later measurements are reported separately.
