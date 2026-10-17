from ripple.evidence import resolve_sources
from ripple.fixtures import initial_sources, migration_source, source


def test_a_late_older_fact_cannot_replace_newer_effective_knowledge():
    current = migration_source()
    old = next(s for s in initial_sources("outdated-fix") if s["id"] == "compatibility")
    for arrival_order in [[current, old], [old, current]]:
        records = resolve_sources(arrival_order)
        assert next(s for s in records if s["id"] == "migration")["active"]
        superseded = next(s for s in records if s["id"] == "compatibility")
        assert superseded["active"] is False
        assert superseded["superseded_by"] == "migration"


def test_equal_effective_times_resolve_deterministically_without_arrival_precedence():
    a = source("a", "A", "Fact A", "2026-10-16T08:00:00Z", fact_key="same")
    b = source("b", "B", "Fact B", "2026-10-16T08:00:00Z", fact_key="same")
    assert {s["id"] for s in resolve_sources([a, b]) if s["active"]} == {"b"}
    assert {s["id"] for s in resolve_sources([b, a]) if s["active"]} == {"b"}
