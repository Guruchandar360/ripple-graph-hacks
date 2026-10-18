"""Export a read-only console. Recorded graphs come only from actual run artifacts."""

import argparse
import json
import re
import shutil
from pathlib import Path

from ripple.fixtures import SCENARIOS, initial_sources, new_state
from ripple.readiness import checklist
from ripple.repository import projection

ROOT = Path(__file__).resolve().parent.parent


def export(destination: Path):
    destination.mkdir(parents=True, exist_ok=True)

    def write(name, data):
        (destination / f"{name}.json").write_text(
            json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
        )

    records = ROOT / "artifacts"
    if not (records / "evaluations.json").exists():
        records = ROOT / "demo"
    evaluations = records / "evaluations.json"
    write("scenarios", SCENARIOS)
    write(
        "health",
        {
            "database": "unavailable",
            "model": "Read-only showcase",
            "model_configured": False,
            "limits": {"workspace_daily": 0, "global_daily": 0},
        },
    )
    write(
        "evaluations",
        json.loads(evaluations.read_text(encoding="utf-8"))
        if evaluations.exists()
        else {"measured": False, "cases": [], "summary": None},
    )
    replays = [
        {**json.loads(p.read_text(encoding="utf-8")), "replay": True}
        for p in sorted((records / "replays").glob("*.json"))
    ]
    proof_index = ROOT / "demo/proof-index.json"
    if proof_index.exists():
        for filename in ("proof-index.json", "proof-audit.json", "repeatability.json"):
            shutil.copyfile(ROOT / "demo" / filename, destination / filename)
        shutil.copyfile(ROOT / "demo/verification/ci-results.txt", destination / "ci-results.txt")
        indexed = json.loads(proof_index.read_text(encoding="utf-8"))
        proof_records = destination / "proof-records"
        proof_records.mkdir(exist_ok=True)
        for name in indexed["benchmark_replays"] + indexed["sequence_replays"]:
            if not re.fullmatch(r"demo/replays/[a-f0-9]{32}\.json", name):
                raise ValueError("Unexpected proof recording path")
            shutil.copyfile(ROOT / name, proof_records / Path(name).name)
        if indexed.get("live_http_report"):
            if indexed["live_http_report"] != "demo/live/http-proof.json" or not re.fullmatch(
                r"demo/live/[a-f0-9]{32}\.json", indexed["live_http_replay"]
            ):
                raise ValueError("Unexpected native HTTP proof path")
            shutil.copyfile(ROOT / indexed["live_http_report"], destination / "native-http-proof.json")
            shutil.copyfile(ROOT / indexed["live_http_replay"], destination / "native-http-replay.json")
        if indexed.get("native_sequence_report"):
            if indexed["native_sequence_report"] != "demo/live/sequence/repeatability.json":
                raise ValueError("Unexpected native sequence report path")
            shutil.copyfile(ROOT / indexed["native_sequence_report"], destination / "native-sequence.json")
            native_records = []
            for name in indexed["native_sequence_replays"]:
                if not re.fullmatch(r"demo/live/sequence/replays/[a-f0-9]{32}\.json", name):
                    raise ValueError("Unexpected native sequence recording path")
                shutil.copyfile(ROOT / name, proof_records / Path(name).name)
                native_records.append(
                    {**json.loads((ROOT / name).read_text(encoding="utf-8")), "replay": True}
                )
            native_records.sort(
                key=lambda r: {"recovery": 0, "memory": 1, "insufficient": 2}[r["demonstration_phase"]]
            )
            replays = native_records + replays
    write("replays", replays)
    featured = next(
        (
            r
            for r in replays
            if r.get("mode") == "graph"
            and r.get("status") == "recovered"
            and r.get("evaluation_case") == "C02"
        ),
        next((r for r in replays if r.get("mode") == "graph" and r.get("status") == "recovered"), None),
    )
    write("featured", featured)
    memories = {
        n["id"]: n["data"]
        for r in replays
        for n in r["graph"]["nodes"]
        if n.get("label") == "Incident" and n["id"].startswith("memory-")
    }
    write("memory", list(memories.values()))
    write("readiness", checklist(ROOT, graph_connected=False, model_configured=False))
    for scenario in SCENARIOS:
        state = new_state()
        state.update(scenario=scenario, sources=initial_sources(scenario["id"]))
        nodes, edges = projection(state)
        write(
            f"preview-{scenario['id']}",
            {"preview": True, "scenario": scenario, "graph": {"nodes": nodes, "edges": edges}},
        )
    for extension in ("webm", "mp4"):
        video = ROOT / "demo" / f"ripple-demo.{extension}"
        if video.exists():
            shutil.copyfile(video, destination / video.name)
    for filename in ("ripple-demo.srt", "video.json", "film-script.json"):
        if (ROOT / "demo" / filename).exists():
            shutil.copyfile(ROOT / "demo" / filename, destination / filename)
    print(f"Exported read-only showcase to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "frontend/public/showcase")
    export(parser.parse_args().output)
