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
