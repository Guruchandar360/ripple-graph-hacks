"""Executable synthetic runtime. Never handed wholesale to the model."""

from copy import deepcopy

from ripple.models import DomainError


def seed(scenario: str) -> dict:
    return {
        "deployment": "v2.4",
        "schema": 2,
        "strict_currency_validation": scenario != "insufficient",
        "origin_unavailable": scenario == "insufficient",
        "restarts": {},
        "executions": 0,
    }


def probe(runtime: dict, service: str, dependencies: list[list[str]]) -> dict:
    def health(target: str, visited: set[str]) -> tuple[bool, str]:
        if target in visited:
            return True, "Already inspected"
        visited = visited | {target}
        if target == "payments":
            if runtime["origin_unavailable"]:
                return False, "Origin diagnostics unavailable; root cause unconfirmed"
            if runtime["deployment"] == "v2.3" and runtime["schema"] == 2:
                return False, "Deployment cannot read current ledger schema"
            if runtime["strict_currency_validation"]:
                return False, "Legacy currency rejected by strict validation"
        if target == "ledger" and runtime["origin_unavailable"]:
            return False, "Origin diagnostics unavailable; root cause unconfirmed"
        for caller, dependency in dependencies:
            if caller == target:
                ok, detail = health(dependency, visited)
                if not ok:
                    return False, f"Dependency {dependency}: {detail}"
        return True, "Synthetic request completed successfully"

    ok, detail = health(service, set())
    return {
        "service": service,
        "healthy": ok,
        "status_code": 200 if ok else 503,
        "detail": detail,
        "synthetic": True,
    }


def execute(runtime: dict, action: str, target: str) -> dict:
    result = deepcopy(runtime)
    if action == "rollback_deployment":
        if target != "payments":
            raise DomainError("No rollback artifact is available for this service.", code="action_blocked")
        if result["schema"] != 1:
            raise DomainError(
                "Runtime precondition failed: v2.3 cannot read ledger schema 2.", code="action_blocked"
            )
        result["deployment"] = "v2.3"
        result["strict_currency_validation"] = False
    elif action == "disable_feature_flag":
        if target != "payments" or not result["strict_currency_validation"]:
            raise DomainError("No active supported flag exists on this target.", code="action_blocked")
        result["strict_currency_validation"] = False
    elif action == "restart_service":
        result["restarts"][target] = result["restarts"].get(target, 0) + 1
    else:
        raise DomainError("Unsupported simulator action.", code="action_blocked")
    result["executions"] += 1
    return result
