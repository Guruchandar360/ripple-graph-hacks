# Understand and explain Ripple

This guide supports your own technical review. Reading it is not an automatic
attestation, and no code or UI can establish your personal eligibility.

## Explain the product in your own words

Ripple investigates a synthetic checkout incident. It reads connected operational
evidence, proposes a bounded recovery action, and verifies the result using request
probes. Human approval, current graph policy and physical simulator preconditions
are separate checks. It is not connected to a real company's infrastructure.

## Trace one complete investigation

1. A visitor receives an HttpOnly workspace cookie. The server uses it to select
   an isolated FalkorDB graph; it never accepts an arbitrary graph name from the model.
2. Loading a scenario persists six services, their dependency/ownership edges,
   source records, action policies, and private simulator state.
3. The investigator starts a fresh conversation. Its tools query native paths,
   active source context, applicable policy edges, and related incident outcomes.
4. A proposal must cite evidence retrieved during that run, and its target must
   have been probed. Evidence is not treated as an instruction to execute code.
5. Current `Constraint` nodes link through `BLOCKS` or `PERMITS` to supported
   action templates. These relationships influence both proposal and execution.
6. Approval checks evidence revision and scenario generation. A pure simulator
   transition and its audit record commit together with a snapshot version check.
7. Checkout's user-facing path and the target's blast radius are probed. Success
   requires a previously failing check and all required checks passing afterward.
8. The measured outcome is saved as incident memory. A new conversation can
   retrieve it, but it must check current applicability again.

## Explain the signature scenario

The last received advisory reports schema 1 and permits rollback; it does not
approve a flag-only mitigation. The simulator's physical runtime is already on
schema 2, representing a late-arriving migration report. This separation is
intentional: the model cannot read hidden fault configuration.

A newer schema 2 advisory supersedes the old one by **effective time**, regardless
of arrival order. The graph now blocks rollback and permits the flag mitigation.
Old approvals become stale. A physical precondition also blocks an incompatible
rollback even if someone tries executing before the new advisory arrives.

The actual model is not forced to recommend rollback initially; it may request
more evidence. Do not script or edit its output to pretend it made a decision.

## Questions you should be able to answer

- What does the graph do that the visual diagram alone cannot do?
- Which direction do dependency edges point, and how does incoming traversal find impact?
- Why is a dependency path not proof of causality?
- Where do `BLOCKS` and `PERMITS` policies come from?
- What is the difference between effective time and ingestion time?
- Why do storage version, evidence revision, and scenario generation differ?
- Why is repeating an action ID safe in this simulator?
- What happens if the model hallucinates a source ID or proposes an unsupported action?
- Which tests use doubles, which use real FalkorDB, and which invoke a real model?
- What does the baseline receive, and why does the comparison not prove universal superiority?
- Which aspects of this project would need redesign for production?

## Known limits to explain honestly

The company and incidents are synthetic. Only three recovery actions exist.
The backend uses one worker and rebuilds a small graph projection on mutation.
The model can choose poorly; deterministic guards do not prove model intelligence.
Equal effective timestamps use a deterministic ID tie-break, not a complete trust
or conflict adjudication system. Gemini requires your own configured access.
Ollama is an explicit optional local provider, never a hidden cloud fallback.

## Record your contribution

Review the implementation, run the real setup, change or extend a meaningful
scenario, inspect the essential queries, and record what you personally verified.
Keep the README AI-assistance disclosure. Do not claim a test, benchmark, feature,
or personal contribution that you have not actually performed.
