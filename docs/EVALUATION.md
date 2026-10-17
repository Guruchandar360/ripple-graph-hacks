# Evaluation methodology

Run `python -m ripple.evaluate --cases 1 --mode both` with actual model and graph
access. The executable 12-case matrix lives in `ripple/evaluate.py`; no evaluator
answers are exposed to agent tools. Default is one case in both modes to avoid
silently consuming a large free quota. Provider access is never mocked here.

Modes use the same model, source records, available simulator probes/actions,
temperature, and maximum turn count. Graph mode additionally retrieves connected
paths and incident memory. The full-document baseline receives all active fixture
documents, including the textual dependency catalog, without graph traversal or
incident-memory retrieval. This comparison measures the configured workflows,
not an isolated causal estimate of the database's contribution.

Current source documents are loaded before the first model call in both modes.
Graph mode also preloads persisted outcomes through the native memory query.
Preloading is explicitly attributed to application code, never to a model tool
decision. Memory retrieval and memory citation are reported separately: an outcome
being available does not prove that it caused the model's recommendation.
Completed deterministic snapshot reads are removed from later tool choices;
proposals are limited to targets probed in the current investigation. The server
independently validates target probes. These guards do not choose a recovery
action or disclose evaluator answers. The release agent matches the measured
combined configuration at `2c8aaaa`; the unrestricted variant's complete 20/24
report is retained separately in `demo/development/open-reads-suite.json`.

Cases cover known/late migration, ingestion order, changed topology, unrelated
telemetry, failed historical recovery, verified memory, fresh conversation,
inapplicable memory, missing diagnostics, misleading advice, and old ownership.
Some bootstrap memories are deterministic simulator executions, explicitly
identified as evaluator history rather than model-generated prior incidents.

Record mode, final status, expected outcome, reported impact, citations, calls,
elapsed time, blocked proposals, executed violations, and stale approval rejection.
A shared execution guard may prevent a bad model proposal; report rejected
proposals separately from execution violations. Success claims require actual
healthy post-action probes. The late-evidence case includes two investigations;
call/time figures include both, and the second gets its own bounded turn budget.

Limitations: small synthetic sample, nondeterministic model output, provider
quota/time effects, and graph mode's additional memory capability. Run multiple
repetitions before making comparisons. UI scores remain absent until a real
artifact is generated. Do not present unit-test doubles as live benchmark runs.

The fixtures used during development are not held-out data. The initial Qwen3
1.7B smoke result is preserved under `demo/development/`; it is not silently
replaced by a later model's score. A newer model/prompt is a different measurement.
Ollama CPU evaluation explicitly uses a 300-second window; the application's
normal window is 120 seconds. Provider/model identity and these limits must
accompany the results. No Gemini performance is inferred from Ollama output.

The full GitHub Actions evaluation splits the 12 cases across four independent
Linux runners, each with its own real FalkorDB and Ollama containers. Each runner
executes graph and baseline modes sequentially with the same configuration.
`ripple.merge_evaluations` retains every row, rejects duplicates and marks missing
runs as an incomplete sample. Cases within a shard have their own isolated
workspace graphs; memory bootstrap happens inside each case that needs history.

The optional local `json` protocol constrains tool-call syntax, not decisions.
Its model selects the tools, arguments, citations and proposed action. Both modes
use the same selected protocol. Native Gemini calling remains the default live
configuration. Reports identify this difference explicitly.

Expected impact is computed from all six simulator request probes **before** any
remediation, exclusively inside the evaluator. An incomplete model-reported
impact set is marked incorrect even if its action recovers the system. The UI
shows impact accuracy and execution violations alongside outcome success.
`expected_met` checks the expected terminal state (and whether an exercised
stale approval was rejected). Citation validity and impact correctness are
separate metrics; a recovered incident can still have an incomplete reported
impact set. A green recovery result is not a claim that every metric passed.

For a late evidence case, a model may legitimately ask for updated diagnostics
instead of proposing an action. `stale_approval_rejected=null` means there was no
approval to exercise; it is not counted as a rejection. The real integration test
separately verifies that an actual stale approval cannot execute.
