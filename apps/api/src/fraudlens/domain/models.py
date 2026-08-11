from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Finding(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    agent: str
    code: str
    title: str
    explanation: str
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    risk_points: int = Field(ge=0, le=100)
    evidence_ids: list[str] = Field(min_length=1)
    deterministic: bool = True


class Evidence(BaseModel):
    id: str
    kind: str
    source: str
    attributes: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)
    sha256: str | None = None


class InvestigationRequest(BaseModel):
    case_id: str = Field(min_length=3, max_length=100)
    tenant_id: str = Field(default="demo", min_length=2, max_length=100)
    evidence: list[Evidence] = Field(min_length=1, max_length=100)
    enable_llm_summary: bool = True


class AgentTrace(BaseModel):
    agent: str
    status: str
    duration_ms: int
    finding_count: int


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    severity: Severity
    ruleset_version: str
    finding_ids: list[UUID]


class InvestigationReport(BaseModel):
    investigation_id: UUID = Field(default_factory=uuid4)
    case_id: str
    tenant_id: str
    status: str = "COMPLETED"
    risk: RiskAssessment
    findings: list[Finding]
    summary: str
    citations: list[str]
    agent_trace: list[AgentTrace]
    requires_human_review: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def citations_must_reference_evidence(self) -> "InvestigationReport":
        allowed = {evidence_id for item in self.findings for evidence_id in item.evidence_ids}
        if not set(self.citations).issubset(allowed):
            raise ValueError("Report citations must reference finding evidence")
        return self
