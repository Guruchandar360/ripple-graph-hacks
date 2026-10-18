"""Audit recorded evidence without a model call, database connection or credential.

This checks artifact consistency, not authenticity of external execution or live
deployment readiness. --online additionally checks the cited GitHub run metadata.
"""

import argparse
import hashlib
import json
import re
import statistics
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "Guruchandar360/ripple-graph-hacks"


class ProofError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProofError(message)


def artifact(root, name):
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), f"Artifact escapes the project: {name}")
    require(path.is_file(), f"Missing artifact: {name}")
    return path


def read(root, name):
    return json.loads(artifact(root, name).read_text(encoding="utf-8"))


def fingerprint(path):
    data = path.read_bytes()
    # Git may check text out with CRLF on Windows. Binary media stays byte-exact.
    if path.suffix in {".json", ".xml", ".txt", ".mjs"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def verify_hashes(root, hashes):
    for name, expected in hashes.items():
        actual = fingerprint(artifact(root, name))
        require(actual == expected, f"Checksum mismatch: {name}")


def verify_recovery(result):
    require(result.get("verified") is True, "Recovery is not marked verified")
    before, after = result.get("before", []), result.get("after", [])
    require(before and after, "Recovery probes are missing")
    before_ids, after_ids = [p["service"] for p in before], [p["service"] for p in after]
    require(len(set(before_ids)) == len(before_ids), "Duplicate before probe")
    require(len(set(after_ids)) == len(after_ids), "Duplicate after probe")
    require(set(before_ids) == set(after_ids), "Recovery probe coverage changed")
    require(any(p["healthy"] is False and p["status_code"] >= 400 for p in before), "No failing before probe")
    require(
        all(p["healthy"] is True and p["status_code"] == 200 for p in after),
        "After probes do not prove recovery",
    )


def verify_record(record):
    nodes = {n["id"]: n for n in record["graph"]["nodes"]}
    edges = {e["id"]: e for e in record["graph"]["edges"]}
    paths = 0
    for event in record["events"]:
        for path in event.get("paths", []):
            ids, relations = path["nodes"], path["edges"]
            require(ids and len(relations) == len(ids) - 1, "Malformed supporting path")
            require(all(nodes.get(n, {}).get("label") == "Service" for n in ids), "Path service is absent")
            for start, end, relation in zip(ids, ids[1:], relations):
                edge = edges.get(relation, {})
                require(
                    edge.get("kind") == "DEPENDS_ON"
                    and edge.get("source") == start
                    and edge.get("target") == end,
                    "Supporting path disagrees with its archived graph",
                )
            paths += 1
    require(record["model_calls"] > 0, "Recorded investigation contains no model calls")
    if record["mode"] == "graph":
        require(paths > 0, "Graph investigation has no recorded supporting paths")
    else:
        require(not paths and not record["memory_ids"], "Baseline retrieved graph paths or memory")
        require(
            not any(t["name"] in {"get_impact", "retrieve_memory"} for t in record["completed_tools"]),
            "Baseline used a disabled graph tool",
        )
    executed = [p for p in record["proposals"] if p.get("result")]
    for proposal in executed:
        require(
            not proposal["blocked_reason"] and not proposal["stale"], "A blocked or stale action executed"
        )
        require(proposal["result"]["action_id"] == proposal["id"], "Action result ID does not match")
        if proposal["result"]["verified"]:
            verify_recovery(proposal["result"])
    verified = [p for p in executed if p["result"]["verified"]]
    require(
        (record["status"] == "recovered") == bool(verified), "Recovery status disagrees with executed probes"
    )
    return {"paths": paths, "executed": executed, "verified": verified}


def observed_impact(record):
    nodes = {n["id"]: n for n in record["graph"]["nodes"]}
    observations = {}
    for event in record["events"]:
        if (
            event.get("source_run_id", record["id"]) == record["id"]
            and event.get("origin") == "application_preflight"
            and event["title"].endswith("probe completed")
        ):
            for sid in event["evidence_ids"]:
                data = nodes.get(sid, {}).get("data", {})
                require(type(data.get("healthy")) is bool, "Preflight probe receipt is missing")
                observations[data["service"]] = data["healthy"]
    services = {n["id"] for n in nodes.values() if n["label"] == "Service"}
    require(set(observations) == services and len(services) == 6, "Preflight did not cover all six services")
    return {service for service, healthy in observations.items() if not healthy}


def current_proposals(record):
    return [
        p
        for p in record["proposals"]
        if p["revision"] == record["revision"] and p["generation"] == record["generation"]
    ]


def conclusion_citations(record):
    return [sid for p in current_proposals(record) for sid in p["evidence_ids"]] + (
        record["diagnosis"] or {}
    ).get("evidence_ids", [])


def verify_benchmark(report, records):
    require(report.get("complete") is True and len(report["cases"]) == 24, "Benchmark is incomplete")
    require(len(records) == 24, "Benchmark replay coverage is incomplete")
    indexed = {(r["evaluation_case"], r["mode"]): r for r in records}
    require(len(indexed) == 24, "Duplicate benchmark replay case/mode")
    expected_pairs = {(f"C{n:02d}", mode) for n in range(1, 13) for mode in ("graph", "baseline")}
    require(set(indexed) == expected_pairs, "The full 12-case paired sample is missing")
    require(
        {(r["case"], r["mode"]) for r in report["cases"]} == expected_pairs,
        "Benchmark rows are duplicated or missing",
    )
    path_count = 0
    for row in report["cases"]:
        record = indexed[(row["case"], row["mode"])]
        require(
            record["model"] == report["model"] and record["model_provider"] == report["model_provider"],
            "Model identity differs",
        )
        require(record["tool_protocol"] == report["tool_protocol"], "Tool protocol differs")
        checked = verify_record(record)
        path_count += checked["paths"]
        for field in ("status", "model_calls", "elapsed_ms"):
            require(row[field] == record[field], f"Benchmark {field} disagrees with replay")
        proposals = current_proposals(record)
        allowed = next((p for p in reversed(proposals) if not p["blocked_reason"] and not p["stale"]), None)
        reported_impact = set((allowed or record["diagnosis"] or {}).get("affected_services", []))
        require(
            row["correct_impact"] == (reported_impact == observed_impact(record)),
            "Impact score disagrees with actual preflight probes",
        )
        citations = conclusion_citations(record)
        require(
            row["valid_citations"] == bool(citations and set(citations) <= set(record["seen_evidence"])),
            "Citation score disagrees with receipts",
        )
        require(row["verified"] == bool(checked["verified"]), "Recovery score disagrees with probes")
        expected_status = "recovered" if int(row["case"][1:]) <= 8 else "needs_evidence"
        expected_met = record["status"] == expected_status
        if row["case"] == "C02":
            expected_met &= row["stale_approval_rejected"] is not False
        if row["case"] == "C12":
            require(row.get("superseded_owner_excluded") is True, "Superseded ownership was not excluded")
        require(row["expected_met"] == expected_met, "Expected-outcome score disagrees with terminal state")
        require(
            row["invalid_proposals"] == sum(bool(p["blocked_reason"]) for p in proposals),
            "Blocked-proposal count disagrees",
        )
        require(row["executed_violations"] == 0, "Executed policy violation was reported")
    require(
        report["summary"]
        == {
            "runs": 24,
            "expected_met": sum(r["expected_met"] for r in report["cases"]),
            "verified_recoveries": sum(r["verified"] for r in report["cases"]),
        },
        "Benchmark summary disagrees with rows",
    )
    summary = {}
    for mode in ("graph", "baseline"):
        rows = [r for r in report["cases"] if r["mode"] == mode]
        summary[mode] = {
            **{
                field: sum(bool(r[field]) for r in rows)
                for field in ("expected_met", "verified", "correct_impact", "valid_citations")
            },
            "runs": len(rows),
            "median_seconds": statistics.median(r["elapsed_ms"] for r in rows) / 1000,
        }
    return summary, path_count


def verify_sequence(row, phases):
    require(set(phases) == {"recovery", "memory", "insufficient"}, "Sequence phase is missing")
    recovery, memory, insufficient = (phases[p] for p in ("recovery", "memory", "insufficient"))
    require(len({r["id"] for r in phases.values()}) == 3, "Sequence reused a conversation ID")
    require(all(r["mode"] == "graph" for r in phases.values()), "Sequence is not graph mode")
    a, b, c = (verify_record(r) for r in (recovery, memory, insufficient))
    require(a["verified"] and b["verified"], "Sequence recovery lacks healthy probes")
    prior_ids = {p["id"] for p in a["verified"]}
    cited = {sid.removeprefix("memory-") for sid in conclusion_citations(memory) if sid.startswith("memory-")}
    linked = prior_ids & set(memory["memory_ids"]) & cited
    require(linked, "Fresh conversation did not retrieve AND cite its actual prior recovery")
    for action_id in linked:
        mid = f"memory-{action_id}"
        node = next((n for n in memory["graph"]["nodes"] if n["id"] == mid), None)
        require(node and node["data"]["verified"] is True, "Memory is not a verified graph outcome")
        original = next(p for p in a["verified"] if p["id"] == action_id)
        require(
            datetime.fromisoformat(original["result"]["executed_at"])
            < datetime.fromisoformat(memory["created_at"]),
            "Cited recovery did not precede the fresh conversation",
        )
        require(
            node["data"]["result"] == original["result"], "Memory result differs from actual prior execution"
        )
        require(
            any(
                e["kind"] == "LEARNED_FROM" and e["source"] == memory["id"] and e["target"] == mid
                for e in memory["graph"]["edges"]
            ),
            "Native memory relationship is absent",
        )
    require(
        insufficient["status"] == "needs_evidence"
        and not c["executed"]
        and insufficient["diagnosis"]["missing_evidence"],
        "Insufficient-evidence case executed or failed to request diagnostics",
    )
    require(
        any(e["title"] == "Evidence changed" for e in recovery["events"]), "Evidence-change event is missing"
    )
    require(
        any(
            p["stale"] and p["revision"] < recovery["revision"] and not p["result"]
            for p in recovery["proposals"]
        ),
        "Old approval was not invalidated",
    )
    for field in (
        "passed",
        "initial_investigation_completed",
        "actual_previous_model_outcome_retrieved",
        "actual_previous_model_outcome_cited",
        "no_unjustified_execution",
        "stale_approval_rejected",
    ):
        require(row[field] is True, f"Sequence driver assertion failed: {field}")
    require(
        row["recovery"] == recovery["status"]
        and row["memory"] == memory["status"]
        and row["insufficient_evidence"] == insufficient["status"],
        "Sequence summary differs from replays",
    )
    return {
        "repetition": row["repetition"],
        "prior_action_ids_retrieved_and_cited": sorted(linked),
        "supporting_paths_cross_checked": a["paths"] + b["paths"] + c["paths"],
        "passed": True,
    }


def audit(root=ROOT, online=False):
    index = read(root, "demo/proof-index.json")
    verify_hashes(root, index["sha256"])
    receipts = {r["kind"]: r for r in index["workflows"]}
    release = read(root, "demo/release.json")
    for name, kind in (("benchmark", "benchmark"), ("repeatability", "sequences")):
        require(
            release[f"{name}_workflow"] == receipts[kind]["url"]
            and release[f"{name}_source_commit"] == receipts[kind]["source_commit"],
            "Release provenance differs from the indexed workflow/source",
        )
    benchmark = read(root, "demo/evaluations.json")
    stats, path_count = verify_benchmark(benchmark, [read(root, p) for p in index["benchmark_replays"]])
    repeated = read(root, "demo/repeatability.json")
    require(
        repeated["acceptance_version"] == "evidence-first-v2"
        and repeated["complete"] is True
        and repeated["passed"] is True,
        "Strict sequential gate did not pass",
    )
    require(
        [r["repetition"] for r in repeated["cases"]] == [1, 2, 3], "Three sequential attempts are missing"
    )
    phases = [read(root, p) for p in index["sequence_replays"]]
    require(
        all(r["model"] == repeated["model"] and r["model_provider"] == repeated["provider"] for r in phases),
        "Sequence provider/model identity differs",
    )
    require(
        len(phases) == 9 and len({(r["repetition"], r["demonstration_phase"]) for r in phases}) == 9,
        "Sequence records are duplicated or missing",
    )
    sequences = [
        verify_sequence(
            row, {r["demonstration_phase"]: r for r in phases if r["repetition"] == row["repetition"]}
        )
        for row in repeated["cases"]
    ]
    video = read(root, "demo/video.json")
    require(
        all(
            item["workflow"] == receipts["sequences"]["url"]
            and item["source_commit"] == receipts["sequences"]["source_commit"]
            for item in video["records"]
        ),
        "Video provenance differs from the measured sequence",
    )
    require(
        hashlib.sha256(artifact(root, "demo/ripple-demo.mp4").read_bytes()).hexdigest() == video["sha256"],
        "Video checksum differs from decoded artifact",
    )
    require(
        fingerprint(artifact(root, "frontend/scripts/record-demo.mjs")) == video["recorder_sha256"],
        "Video recorder changed after verification",
    )
    require(
        {r["run_id"] for r in video["records"]} <= {r["id"] for r in phases},
        "Video refers to an absent sequence",
    )
    selected = [next(r for r in phases if r["id"] == item["run_id"]) for item in video["records"]]
    require(
        {r["demonstration_phase"] for r in selected} == {"recovery", "memory", "insufficient"}
        and len({r["repetition"] for r in selected}) == 1,
        "Video mixes sequences or omits a phase",
    )
    require(
        len(video["records"]) == 3
        and video["full_decode_verified"] is True
        and 0 < video["duration_seconds"] < 180,
        "Video verification is incomplete",
    )
    http = read(root, "demo/http-proof.json")
    verify_recovery(http["verified_result"])
    require(
        http["passed"] is True
        and http["duplicate_result_identical"] is True
        and http["memory_survived_scenario_reload"] is True
        and http["database_restart_verified"] is True
        and http["foreign_visitor_status"] == 404,
        "Historical HTTP driver assertions failed",
    )
    tests = ET.parse(artifact(root, "demo/verification/backend-tests.xml")).getroot()
    require(
        len(tests.findall(".//testcase")) == 46
        and not tests.findall(".//failure")
        and not tests.findall(".//error")
        and not tests.findall(".//skipped"),
        "Historical native-database CI test receipt differs",
    )
    ci = []
    if online:
        for receipt in index["workflows"]:
            match = re.fullmatch(
                rf"https://github.com/{re.escape(REPOSITORY)}/actions/runs/(\d+)", receipt["url"]
            )
            require(match is not None, "Unexpected workflow destination")
            result = subprocess.run(
                [
                    "gh",
                    "run",
                    "view",
                    match[1],
                    "--repo",
                    REPOSITORY,
                    "--json",
                    "status,conclusion,headSha,url",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            actual = json.loads(result.stdout)
            require(
                actual["status"] == "completed"
                and actual["conclusion"] == "success"
                and actual["headSha"] == receipt["source_commit"],
                "Cited workflow did not succeed at the stated source",
            )
            ci.append(actual)
    return {
        "evidence_audit_passed": True,
        "scope": "Archived artifact consistency and optional GitHub execution metadata; not independent certification, a fresh model run, or live deployment readiness.",
        "benchmark": stats,
        "supporting_paths_cross_checked": path_count
        + sum(s["supporting_paths_cross_checked"] for s in sequences),
        "path_count_scope": "Returned path instances including repeated retrievals across calls/runs; not unique paths or proof of causation.",
        "sequences": sequences,
        "video_sha256_matches": True,
        "checksummed_files": len(index["sha256"]),
        "online_workflows": ci,
        "pending": [
            "Integrated Gemini + Cloud/Render investigation",
            "Production 120-second reliability",
            "Participant registration, contribution/review and final submission",
        ],
        "limitations": [
            "Synthetic known development fixtures; no general superiority established.",
            "Historical HTTP idempotency/isolation/restart and stale-request rejection are recorded driver assertions; the offline audit does not repeat those requests.",
            "Three passing sequences do not assert perfect impact reporting or production reliability.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--online", action="store_true", help="Check public GitHub workflow metadata through gh"
    )
    parser.add_argument("--output", type=Path, help="Write the audit report; otherwise print it")
    args = parser.parse_args()
    try:
        report = audit(online=args.online)
    except (ProofError, KeyError, OSError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"Evidence audit failed: {exc}") from exc
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Evidence audit passed; wrote {args.output}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
