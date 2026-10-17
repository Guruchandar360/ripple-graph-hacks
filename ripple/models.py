from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


def now() -> str:
    return datetime.now(UTC).isoformat()


class DomainError(Exception):
    def __init__(self, message: str, status: int = 409, code: str = "conflict"):
        super().__init__(message)
        self.message, self.status, self.code = message, status, code


class Proposal(BaseModel):
    action: Literal["rollback_deployment", "disable_feature_flag", "restart_service"]
    target: Literal["storefront", "checkout", "payments", "ledger", "inventory", "notifications"]
    summary: str = Field(min_length=12, max_length=1500)
    evidence_ids: list[str] = Field(min_length=1, max_length=20)
    affected_services: list[str] = Field(default_factory=list, max_length=6)


class Diagnosis(BaseModel):
    summary: str = Field(min_length=12, max_length=1500)
    affected_services: list[str] = Field(max_length=6)
    evidence_ids: list[str] = Field(min_length=1, max_length=20)
    missing_evidence: list[str] = Field(default_factory=list, max_length=8)


class StartRun(BaseModel):
    mode: Literal["graph", "baseline"] = "graph"


class EvidenceRequest(BaseModel):
    event: Literal["migration"] = "migration"
