"""Render release measurements from actual artifacts; never generate benchmark rows."""

import json
import statistics
from pathlib import Path

root = Path(__file__).resolve().parent.parent
report = json.loads((root / "demo/evaluations.json").read_text(encoding="utf-8"))
release = json.loads((root / "demo/release.json").read_text(encoding="utf-8"))
rows = report["cases"]
lines = [
    "# Recorded development measurements",
    "",
    f"Model: `{report['model']}`. Provider: `{report['model_provider']}`. "
    f"Tool protocol: `{report['tool_protocol']}`.",
    "",
    f"[Raw benchmark workflow]({release['benchmark_workflow']}) · "
    "[Raw report](../demo/evaluations.json) · [Provenance](../demo/PROVENANCE.md)",
    "",
    f"Recorded runs: **{len(rows)}**. Complete sample: **{report.get('complete', False)}**. "
    f"Configuration: `{json.dumps(report.get('configuration', {}), sort_keys=True)}`.",
    "",
    "| Workflow | Expected terminal state | Verified recovery | Complete impact | Valid citations | Executed violations | Median elapsed | Model calls |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
]
for mode in ("graph", "baseline"):
    sample = [row for row in rows if row["mode"] == mode]
    if not sample:
        continue
    total = len(sample)
    fields = ["expected_met", "verified", "correct_impact", "valid_citations"]
    values = [f"{sum(bool(row[key]) for row in sample)}/{total}" for key in fields]
    violations = sum(row["executed_violations"] for row in sample)
    median = statistics.median(row["elapsed_ms"] for row in sample) / 1000
    calls = sum(row["model_calls"] for row in sample)
    lines.append(f"| {mode} | {' | '.join(values)} | {violations} | {median:.1f}s | {calls} |")
lines += [
    "",
    "Verified recovery is not expected for insufficient-evidence cases. Expected terminal state, "
    "complete impact and citation validity are separate metrics. Zero executed violations also "
    "reflects the independent shared guard; it does not mean the model never proposed an invalid action.",
    "",
    "## Recorded limitations",
    "",
]
failures = [row for row in rows if not row["expected_met"]]
lines += [f"- {row['case']} / {row['mode']}: `{row['status']}` — {row.get('error') or 'Expected terminal state was not met.'}" for row in failures]
if not failures:
    lines.append("Every recorded run reached its expected terminal state in this sample.")
lines += [
    "",
    f"Incomplete impact sets: **{sum(not row['correct_impact'] for row in rows)}/{len(rows)}**. "
    f"Blocked proposals: **{sum(row['invalid_proposals'] for row in rows)}**.",
    "",
    "These are synthetic development fixtures, not held-out data. Graph mode has additional "
    "traversal and incident-memory retrieval; both workflows receive current documents, probes, "
    "the same model and budget. The comparison does not isolate database causality or establish "
    "general superiority. Late-evidence cases have two bounded conversations and report combined time/calls. "
    "CPU runs use 300 seconds per conversation, versus the application's 120-second default. "
    "Gemini remains the default integration but these measurements do not test Gemini.",
]
repeat_path = root / "demo/repeatability.json"
if repeat_path.exists():
    repeat = json.loads(repeat_path.read_text(encoding="utf-8"))
    cases = repeat["cases"]
    lines += [
        "",
        "## Three sequential demonstrations",
        "",
        f"[Raw workflow]({release['repeatability_workflow']}) · [Raw report](../demo/repeatability.json). "
        f"All acceptance checks passed in **{sum(row['passed'] for row in cases)}/{len(cases)}** sequences.",
        "",
        "| Repetition | Recovery | Fresh-session recovery | Prior model outcome retrieved | Prior model outcome cited | Insufficient evidence | Passed |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in cases:
        lines.append(f"| {row['repetition']} | {row['recovery']} | {row['memory']} | "
                     f"{row['actual_previous_model_outcome_retrieved']} | "
                     f"{row.get('actual_previous_model_outcome_cited', 'not measured')} | "
                     f"{row['insufficient_evidence']} | {row['passed']} |")
    lines += [
        "",
        "Graph-mode application preflight retrieves persisted outcomes before the model call; "
        "the timeline identifies this as application work. Retrieval proves availability, while "
        "citation is a separate observed measure. Neither establishes that memory caused the choice. "
        "Earlier failed sequences remain in `demo/development/first-three-sequences.json`.",
    ]
(root / "docs/MEASUREMENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Rendered docs/MEASUREMENTS.md from recorded measurements.")
