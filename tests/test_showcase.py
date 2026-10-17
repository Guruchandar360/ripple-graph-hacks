import json

from ripple import export_showcase


def test_showcase_preserves_recorded_graphs_without_exposing_runtime(tmp_path, monkeypatch):
    root = tmp_path / "root"
    records = root / "demo" / "replays"
    records.mkdir(parents=True)
    original = {
        "id": "real-record",
        "graph": {"nodes": [{"id": "database-proof"}], "edges": []},
        "status": "recovered",
        "model": "explicit-test-provider",
    }
    (records / "real-record.json").write_text(json.dumps(original), encoding="utf-8")
    (root / "demo/evaluations.json").write_text('{"measured": true, "cases": []}', encoding="utf-8")
    monkeypatch.setattr(export_showcase, "ROOT", root)
    destination = tmp_path / "public"
    export_showcase.export(destination)
    replay = json.loads((destination / "replays.json").read_text())[0]
    assert replay["graph"] == original["graph"]
    assert replay["replay"] is True
    assert json.loads((destination / "health.json").read_text())["database"] == "unavailable"
    for path in destination.glob("*.json"):
        data = path.read_text()
        assert '"simulator"' not in data
        assert '"origin_unavailable"' not in data
    readiness = json.loads((destination / "readiness.json").read_text())
    assert not any(c["ready"] for c in readiness["checks"] if c["human_required"])
