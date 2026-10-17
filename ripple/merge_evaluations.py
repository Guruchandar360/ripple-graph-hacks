"""Merge independent real evaluation shards, retaining all measured failures."""

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path


def merge(source: Path, destination: Path, expected_runs: int):
    reports = [json.loads(p.read_text(encoding="utf-8")) for p in source.rglob("evaluations.json")]
    if not reports:
        raise SystemExit("No measured evaluation artifacts were produced.")
    identities = {(r["model"], r["model_provider"]) for r in reports}
    if len(identities) != 1:
        raise SystemExit("Cannot merge different model/provider identities.")
    rows = sorted(
        [row for report in reports for row in report["cases"]], key=lambda r: (r["case"], r["mode"])
    )
    if len({(r["case"], r["mode"]) for r in rows}) != len(rows):
        raise SystemExit("Duplicate case/mode pair; merge would misrepresent the sample.")
    output = {
        **reports[0],
        "created_at": datetime.now(UTC).isoformat(),
        "cases": rows,
        "complete": len(rows) == expected_runs,
        "expected_runs": expected_runs,
        "summary": {
            "runs": len(rows),
            "expected_met": sum(r["expected_met"] for r in rows),
            "verified_recoveries": sum(r["verified"] for r in rows),
        },
    }
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "evaluations.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    (destination / "replays").mkdir(exist_ok=True)
    for path in source.rglob("replays/*.json"):
        shutil.copyfile(path, destination / "replays" / path.name)
    print(json.dumps(output["summary"]))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-runs", type=int, required=True)
    args = parser.parse_args()
    merge(args.source, args.destination, args.expected_runs)
