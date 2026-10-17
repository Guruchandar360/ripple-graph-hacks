"""Resolve fact versions by effective time, never by arrival order."""

from datetime import datetime


def resolve_sources(records: list[dict]) -> list[dict]:
    output = [dict(record) for record in records]
    groups: dict[str, list[dict]] = {}
    for record in output:
        key = record.get("fact_key")
        if key:
            groups.setdefault(key, []).append(record)
    for versions in groups.values():
        candidates = [v for v in versions if not v.get("withdrawn", False)]
        if not candidates:
            continue
        latest = max(
            candidates,
            key=lambda v: (datetime.fromisoformat(v["effective_at"]), v["id"]),
        )
        for version in versions:
            version["active"] = version["id"] == latest["id"]
            if not version["active"]:
                version["superseded_by"] = latest["id"]
            else:
                version.pop("superseded_by", None)
    return output


def policy_records(records: list[dict], action: str, target: str) -> list[dict]:
    """Pure representation used by fixture inspection and explicit test doubles."""
    return [
        {**rule, "source_id": record["id"], "effective_at": record["effective_at"]}
        for record in records
        if record.get("active")
        for rule in record.get("policies", [])
        if rule["action"] == action and rule["target"] in {target, "*"}
    ]
