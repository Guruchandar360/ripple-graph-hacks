"""Evidence-based submission checklist. Never infers personal eligibility."""

import json
from pathlib import Path


def checklist(root: Path, *, graph_connected: bool, model_configured: bool) -> dict:
    manifest_path = root / "submission.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    video = manifest.get("video_path")
    video_ready = bool(
        video
        and (root / video).is_file()
        and manifest.get("video_kind") in {"live_agent", "actual_agent_replay"}
    )
    evaluation = root / "artifacts" / "evaluations.json"
    if not evaluation.exists():
        evaluation = root / "demo" / "evaluations.json"
    measured = False
    if evaluation.exists():
        measured = bool(json.loads(evaluation.read_text(encoding="utf-8")).get("measured"))
    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    items = [
        (
            "repository",
            "Public source repository",
            bool(manifest.get("repository_url")),
            "Source, tests and deployment configuration are published."
            if manifest.get("repository_url")
            else "Publish the reviewed source and set the public repository URL.",
            manifest.get("repository_url"),
        ),
        (
            "setup",
            "Reproducible setup & graph model",
            (root / "docs/GRAPH.md").exists() and bool(readme),
            "Local instructions, native graph relationships and essential Cypher are documented.",
            None,
        ),
        (
            "data",
            "Synthetic demonstration data",
            True,
            "Northstar Commerce is fictional. The committed scenarios contain no private company records.",
            None,
        ),
        (
            "ai",
            "AI assistance disclosure",
            "AI assistance disclosure" in readme,
            "The README explicitly describes AI assistance and the participant's review responsibility.",
            None,
        ),
        (
            "graph",
            "Live FalkorDB connection",
            graph_connected,
            "The current server can execute a native graph query."
            if graph_connected
            else "Configure a FalkorDB server. Fixture preview cannot satisfy live graph verification.",
            None,
        ),
        (
            "model",
            "Live model access",
            False,
            "A provider is configured; current availability depends on its quota. Historical native proof is separate from present access."
            if model_configured
            else "This server has no live provider configured. Recorded model runs are in Results; configure Gemini or Ollama for a new investigation.",
            None,
        ),
        (
            "evaluation",
            "Measured graph / baseline results",
            measured,
            "Actual evaluation output is available."
            if measured
            else "Run the real evaluation suite; no scores are invented.",
            None,
        ),
        (
            "video",
            "Working agent demo video",
            video_ready,
            "A recording of actual agent output is attached. Recorded replays are labeled."
            if video_ready
            else "Record the configured live agent. A simulator-only walkthrough must be labeled separately.",
            None,
        ),
        (
            "registration",
            "Registration & team eligibility",
            bool(manifest.get("registration_verified")),
            "The participant must complete and verify registration on WeMakeDevs.",
            "https://www.wemakedevs.org/hackathons/falkordb",
        ),
        (
            "review",
            "Participant technical review",
            bool(manifest.get("participant_review_verified")),
            "Read the contributor guide and explain the graph, tools, guards and limitations in your own words.",
            None,
        ),
    ]
    checks = [
        {
            "id": sid,
            "title": title,
            "ready": bool(ready),
            "detail": detail,
            "url": url,
            "human_required": sid in {"registration", "review"},
        }
        for sid, title, ready, detail, url in items
    ]
    return {
        "name": "Ripple",
        "primary_track": manifest.get("primary_track"),
        "deadline": "2026-10-18T23:59:00+05:30",
        "checks": checks,
        "ready": sum(c["ready"] for c in checks),
        "total": len(checks),
        "deployment_url": manifest.get("deployment_url"),
        "verification": manifest.get("verification"),
        "note": "Preparation status is not an organizer's eligibility approval.",
    }
