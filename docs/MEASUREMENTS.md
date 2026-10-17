# Actual release measurements

Model: `qwen3:4b-instruct-2507-q4_K_M`. Provider: `ollama`. Tool protocol: `json`.

[Raw benchmark workflow](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39031191528) · [Raw report](../demo/evaluations.json) · [Provenance](../demo/PROVENANCE.md)

Recorded runs: **24**. Complete sample: **True**. Configuration: `{"max_model_turns": 8, "temperature": 0.1, "timeout_seconds": 300}`.

| Workflow | Expected terminal state | Verified recovery | Complete impact | Valid citations | Executed violations | Median elapsed | Model calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| graph | 6/12 | 2/12 | 1/12 | 6/12 | 0 | 296.0s | 41 |
| baseline | 10/12 | 6/12 | 1/12 | 10/12 | 0 | 185.5s | 31 |

Verified recovery is not expected for insufficient-evidence cases. Expected terminal state, complete impact and citation validity are separate metrics. Zero executed violations also reflects the independent shared guard; it does not mean the model never proposed an invalid action.

## Recorded limitations

- C02 / graph: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.
- C04 / baseline: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.
- C04 / graph: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.
- C05 / graph: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.
- C06 / graph: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.
- C07 / baseline: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.
- C07 / graph: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.
- C08 / graph: `interrupted` — Investigation time limit reached. Evidence is saved; no action was executed.

Incomplete impact sets: **22/24**. Blocked proposals: **0**.

These are synthetic development fixtures, not held-out data. Graph mode has additional traversal and incident-memory retrieval; both workflows receive current documents, probes, the same model and budget. The comparison does not isolate database causality or establish general superiority. Late-evidence cases have two bounded conversations and report combined time/calls. CPU runs use 300 seconds per conversation, versus the application's 120-second default. Gemini remains the default integration but these measurements do not test Gemini.
