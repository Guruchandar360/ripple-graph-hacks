"""Export a read-only console. Recorded graphs come only from actual run artifacts."""

import argparse
import json
import shutil
from pathlib import Path

from ripple.fixtures import SCENARIOS, initial_sources, new_state
from ripple.readiness import checklist
from ripple.repository import projection

ROOT = Path(__file__).resolve().parent.parent


def export(destination: Path):
    destination.mkdir(parents=True, exist_ok=True)

    def write(name, data):
        (destination / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

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
    write("replays", replays)
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
    video = ROOT / "demo" / "ripple-demo.webm"
    if video.exists():
        shutil.copyfile(video, destination / "ripple-demo.webm")
    print(f"Exported read-only showcase to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "frontend/public/showcase")
    export(parser.parse_args().output)
