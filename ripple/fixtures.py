"""Synthetic public fixture. No evaluator answers or simulator fault labels here."""

from copy import deepcopy

from ripple.evidence import resolve_sources
from ripple.models import now

SERVICES = [
    {"id": "storefront", "name": "Storefront", "kind": "edge", "owner": "experience", "x": 20, "y": 145},
    {"id": "checkout", "name": "Checkout", "kind": "api", "owner": "commerce", "x": 245, "y": 145},
    {"id": "payments", "name": "Payments", "kind": "worker", "owner": "commerce", "x": 480, "y": 35},
    {"id": "inventory", "name": "Inventory", "kind": "api", "owner": "platform", "x": 480, "y": 260},
    {"id": "ledger", "name": "Ledger", "kind": "database", "owner": "platform", "x": 715, "y": 35},
    {
        "id": "notifications",
        "name": "Notifications",
        "kind": "worker",
        "owner": "experience",
        "x": 715,
        "y": 260,
    },
]
DEPENDENCIES = [
    ("storefront", "checkout"),
    ("checkout", "payments"),
    ("checkout", "inventory"),
    ("payments", "ledger"),
    ("inventory", "notifications"),
]
SCENARIOS = [
    {
        "id": "outdated-fix",
        "number": "01",
        "name": "Yesterday’s fix",
        "tag": "CHANGING EVIDENCE",
        "description": "Checkout is failing after a payments release. A familiar rollback may no longer be safe.",
        "incident": "INC-2041",
        "symptom": "Checkout requests return HTTP 500 after payments v2.4.",
    },
    {
        "id": "memory",
        "number": "02",
        "name": "A familiar failure",
        "tag": "PERSISTENT MEMORY",
        "description": "A new incident. An empty conversation. Can a verified past outcome help?",
        "incident": "INC-2042",
        "symptom": "Checkout requests fail with currency validation errors after a new release.",
    },
    {
        "id": "insufficient",
        "number": "03",
        "name": "Know what you don’t know",
        "tag": "INSUFFICIENT EVIDENCE",
        "description": "Checkout is failing, but telemetry is incomplete. An honest agent should ask for evidence.",
        "incident": "INC-2043",
        "symptom": "Checkout requests return HTTP 503. Origin telemetry is unavailable.",
    },
]


def source(sid: str, title: str, text: str, effective: str, **extra) -> dict:
    return {
        "id": sid,
        "title": title,
        "text": text,
        "effective_at": effective,
        "ingested_at": now(),
        "active": True,
        **extra,
    }


def initial_sources(scenario: str) -> list[dict]:
    items = [
        source(
            "topology",
            "Service catalog · dependencies",
            "Storefront depends on checkout. Checkout depends on payments and inventory. "
            "Payments depends on ledger. Inventory depends on notifications. "
            "Commerce owns checkout and payments; Platform owns inventory and ledger; "
            "Experience owns storefront and notifications.",
            "2026-10-15T08:00:00Z",
        ),
        source(
            "alert",
            "Checkout synthetic monitor",
            next(s["symptom"] for s in SCENARIOS if s["id"] == scenario),
            "2026-10-16T09:02:00Z",
        ),
    ]
    if scenario == "insufficient":
        items.append(
            source(
                "telemetry-gap",
                "Observability incident",
                "Payments and ledger diagnostics cannot be collected. No confirmed deployment, "
                "feature-flag, or resource-exhaustion evidence explains the HTTP 503. "
                "Obtain origin logs and request traces before choosing remediation.",
                "2026-10-16T09:03:00Z",
                policies=[
                    {
                        "action": action,
                        "target": "*",
                        "allowed": False,
                        "reason": "Origin diagnostics are missing; no supported action is justified by current evidence.",
                    }
                    for action in ["rollback_deployment", "disable_feature_flag", "restart_service"]
                ],
            )
        )
    else:
        items.extend(
            [
                source(
                    "deployment",
                    "Payments v2.4 release record",
                    "Payments v2.4 enabled strict_currency_validation. Checkout still sends legacy currency "
                    "strings. The previous v2.3 release predates ledger schema 2. "
                    "Both rollback and a runtime flag change require the current compatibility advisory.",
                    "2026-10-16T09:00:00Z",
                ),
                source(
                    "old-runbook",
                    "INC-1988 · historical recovery",
                    "Last month payments validation errors were resolved by rolling back to v2.3. "
                    "That incident used ledger schema 1. This is historical evidence, not proof of "
                    "current compatibility. Verify the ledger schema before rollback.",
                    "2026-09-20T11:00:00Z",
                ),
                source(
                    "flag-config",
                    "Payments runtime configuration",
                    "strict_currency_validation=true. Toggle is scoped to payments. "
                    "Disabling it restores acceptance of legacy currency strings, but requires a current safety advisory. "
                    "Verify downstream checkout and storefront probes after any change.",
                    "2026-10-16T09:01:00Z",
                    record_type="flag_config",
                    flag_enabled=True,
                ),
                source(
                    "compatibility",
                    "Last received ledger compatibility advisory",
                    "The last received signed advisory reports ledger schema 1 as of 08:00 UTC. "
                    "It permits rollback to payments v2.3. A flag-only mitigation has not been approved "
                    "in this advisory. A later schema migration may supersede this record; runtime "
                    "preconditions are checked again before any action executes.",
                    "2026-10-16T08:00:00Z",
                    fact_key="payments-ledger-compatibility",
                    policies=[
                        {
                            "action": "rollback_deployment",
                            "target": "payments",
                            "allowed": True,
                            "reason": "The last received schema 1 advisory permits payments v2.3 rollback.",
                        },
                        {
                            "action": "disable_feature_flag",
                            "target": "payments",
                            "allowed": False,
                            "reason": "A flag-only mitigation requires an updated ledger safety advisory.",
                        },
                    ],
                ),
            ]
        )
    if scenario == "memory":
        items.append(migration_source())
    return resolve_sources(items)


def migration_source() -> dict:
    return source(
        "migration",
        "Ledger migration · schema 2 is active",
        "Ledger schema 2 became active at 08:55 UTC. Payments v2.3 is incompatible with schema 2. "
        "Rollback to v2.3 is blocked. Payments v2.4 supports schema 2; its currency flag can "
        "be disabled without rolling back. This supersedes assumptions made in INC-1988.",
        "2026-10-16T08:55:00Z",
        fact_key="payments-ledger-compatibility",
        policies=[
            {
                "action": "rollback_deployment",
                "target": "payments",
                "allowed": False,
                "reason": "Ledger schema 2 blocks payments v2.3. The old rollback procedure is incompatible.",
            },
            {
                "action": "disable_feature_flag",
                "target": "payments",
                "allowed": True,
                "reason": "The schema 2 advisory permits disabling validation while retaining payments v2.4.",
            },
        ],
    )


def new_state() -> dict:
    return {
        "version": 0,
        "revision": 0,
        "generation": "",
        "scenario": None,
        "sources": [],
        "services": deepcopy(SERVICES),
        "dependencies": [list(e) for e in DEPENDENCIES],
        "runs": {},
        "memory": [],
        "simulator": {},
        "created_at": now(),
    }
