"""Negative checks for the evidence auditor; never invoke a model or database."""

import hashlib

import pytest

from ripple.proof import (
    ROOT,
    ProofError,
    artifact,
    audit,
    fingerprint,
    read,
    verify_benchmark,
    verify_hashes,
    verify_record,
    verify_recovery,
    verify_sequence,
)


def sequence():
    index = read(ROOT, "demo/proof-index.json")
    records = [read(ROOT, name) for name in index["sequence_replays"]]
    return {r["demonstration_phase"]: r for r in records if r["repetition"] == 1}


def test_committed_proof_is_consistent_without_credentials_or_network():
    result = audit()
    assert result["evidence_audit_passed"]
    assert len(result["sequences"]) == 3
    assert result["benchmark"]["graph"]["expected_met"] == 12
    assert result["benchmark"]["baseline"]["expected_met"] == 11
    assert result["online_workflows"] == []
    assert "Integrated Gemini + Cloud/Render investigation" in result["pending"]


@pytest.mark.parametrize("corruption", ["unhealthy", "bad_status", "missing_service"])
def test_recovery_claim_requires_complete_healthy_after_probes(corruption):
    result = read(ROOT, "demo/http-proof.json")["verified_result"]
    if corruption == "unhealthy":
        result["after"][0]["healthy"] = False
    elif corruption == "bad_status":
        result["after"][0]["status_code"] = 503
    else:
        result["after"].pop()
    with pytest.raises(ProofError, match="probes|coverage"):
        verify_recovery(result)


def test_supporting_path_must_exist_in_the_archived_graph():
    record = sequence()["recovery"]
    event = next(e for e in record["events"] if any(p["edges"] for p in e.get("paths", [])))
    edge_id = next(p["edges"][0] for p in event["paths"] if p["edges"])
    record["graph"]["edges"] = [e for e in record["graph"]["edges"] if e["id"] != edge_id]
    with pytest.raises(ProofError, match="Supporting path"):
        verify_record(record)


def test_retrieval_alone_cannot_pass_the_memory_citation_claim():
    phases = sequence()
    for proposal in phases["memory"]["proposals"]:
        proposal["evidence_ids"] = [sid for sid in proposal["evidence_ids"] if not sid.startswith("memory-")]
    row = read(ROOT, "demo/repeatability.json")["cases"][0]
    with pytest.raises(ProofError, match="retrieve AND cite"):
        verify_sequence(row, phases)


def test_forged_impact_score_is_rejected_using_recorded_probe_observations():
    index = read(ROOT, "demo/proof-index.json")
    records = [read(ROOT, name) for name in index["benchmark_replays"]]
    report = read(ROOT, "demo/evaluations.json")
    row = next(r for r in report["cases"] if r["mode"] == "graph" and not r["correct_impact"])
    row["correct_impact"] = True
    with pytest.raises(ProofError, match="Impact score"):
        verify_benchmark(report, records)


def test_checksum_change_is_rejected(tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text('{"verified":true}', encoding="utf-8")
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}
    path.write_text('{"verified":false}', encoding="utf-8")
    with pytest.raises(ProofError, match="Checksum mismatch"):
        verify_hashes(tmp_path, hashes)


def test_artifact_manifest_cannot_read_outside_its_project(tmp_path):
    with pytest.raises(ProofError, match="escapes"):
        artifact(tmp_path, "../outside.json")


@pytest.mark.parametrize("extension,normalizes", [(".json", True), (".mp4", False)])
def test_text_checkouts_normalize_line_endings_but_media_remains_byte_exact(tmp_path, extension, normalizes):
    path = tmp_path / f"artifact{extension}"
    path.write_bytes(b"first\r\nsecond\r\n")
    original = fingerprint(path)
    path.write_bytes(b"first\nsecond\n")
    assert (fingerprint(path) == original) == normalizes
