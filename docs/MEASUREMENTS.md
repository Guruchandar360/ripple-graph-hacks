# Recorded development measurements

Model: `qwen3:4b-instruct-2507-q4_K_M`. Provider: `ollama`. Tool protocol: `json`.

[Raw benchmark workflow](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39130562373) · [Raw report](../demo/evaluations.json) · [Provenance](../demo/PROVENANCE.md)

Recorded runs: **24**. Complete sample: **True**. Configuration: `{"evidence_collection": "all_service_probes_preflight", "max_model_turns": 8, "temperature": 0.1, "timeout_seconds": 300}`.

| Workflow | Expected terminal state | Verified recovery | Complete impact | Valid citations | Executed violations | Median elapsed | Model calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| graph | 12/12 | 8/12 | 10/12 | 12/12 | 0 | 206.0s | 20 |
| baseline | 11/12 | 7/12 | 11/12 | 12/12 | 0 | 94.0s | 16 |

Verified recovery is not expected for insufficient-evidence cases. Expected terminal state, complete impact and citation validity are separate metrics. Zero executed violations also reflects the independent shared guard; it does not mean the model never proposed an invalid action.

## Recorded limitations

- C02 / baseline: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.

Incomplete impact sets: **3/24**. Blocked proposals: **4**.

These are synthetic development fixtures, not held-out data. Graph mode has additional traversal and incident-memory retrieval; both workflows receive current documents, probes, the same model and budget. The comparison does not isolate database causality or establish general superiority. Late-evidence cases have two bounded conversations and report combined time/calls. CPU runs use 300 seconds per conversation, versus the application's 120-second default. Gemini remains the default integration but these measurements do not test Gemini.

## Three sequential demonstrations

[Raw workflow](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39033508952) · [Raw report](../demo/repeatability.json). All acceptance checks passed in **1/3** sequences.

| Repetition | Recovery | Fresh-session recovery | Prior model outcome retrieved | Prior model outcome cited | Insufficient evidence | Passed |
|---|---|---|---|---|---|---|
| 1 | recovered | recovered | True | False | needs_evidence | True |
| 2 | recovered | interrupted | True | False | needs_evidence | False |
| 3 | recovered | interrupted | True | False | needs_evidence | False |

Graph-mode application preflight retrieves persisted outcomes before the model call; the timeline identifies this as application work. Retrieval proves availability, while citation is a separate observed measure. Neither establishes that memory caused the choice. Earlier failed sequences remain in `demo/development/first-three-sequences.json`.
