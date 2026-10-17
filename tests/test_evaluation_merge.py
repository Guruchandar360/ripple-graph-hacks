import json

import pytest

from ripple.merge_evaluations import merge


def test_merge_preserves_failures_and_marks_an_incomplete_sample(tmp_path):
    parts = tmp_path / "parts"
    parts.mkdir()
    for i, mode in enumerate(("graph", "baseline")):
        directory = parts / str(i)
        directory.mkdir()
        report = {
            "model": "same-model",
            "model_provider": "ollama",
            "measured": True,
            "cases": [
                {"case": "C01", "mode": mode, "expected_met": mode == "graph", "verified": mode == "graph"}
            ],
        }
        (directory / "evaluations.json").write_text(json.dumps(report))
    result = merge(parts, tmp_path / "combined", expected_runs=24)
    assert result["complete"] is False
    assert result["summary"] == {"runs": 2, "expected_met": 1, "verified_recoveries": 1}
    assert any(not row["expected_met"] for row in result["cases"])


def test_merge_rejects_duplicate_runs_instead_of_inflating_the_sample(tmp_path):
    for name in ("one", "two"):
        part = tmp_path / name
        part.mkdir()
        (part / "evaluations.json").write_text(
            json.dumps(
                {"model": "m", "model_provider": "ollama", "cases": [{"case": "C01", "mode": "graph"}]}
            )
        )
    with pytest.raises(SystemExit, match="Duplicate"):
        merge(tmp_path, tmp_path / "output", expected_runs=2)
