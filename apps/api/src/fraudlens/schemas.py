from datetime import datetime

from pydantic import BaseModel, Field

from fraudlens.domain.models import Evidence, InvestigationReport


class CaseCreate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,100}$")
    tenant_id: str = Field(default="demo", min_length=2, max_length=100)
    subject: str = Field(min_length=3, max_length=240)
    case_type: str = Field(min_length=2, max_length=80)


class CaseSummary(BaseModel):
    id: str
    tenant_id: str
    subject: str
    case_type: str
    status: str
    risk_score: int
    severity: str
    evidence_count: int
    created_at: datetime
    updated_at: datetime


class CaseDetail(CaseSummary):
    evidence: list[Evidence]
    latest_report: InvestigationReport | None = None


class DashboardMetrics(BaseModel):
    open_cases: int
    critical_cases: int
    high_risk_cases: int
    completed_investigations: int
    average_risk: float
    agent_confidence: float
    priority_cases: list[CaseSummary]


class EvidenceCreate(Evidence):
    pass


class AuditEntry(BaseModel):
    id: str
    actor: str
    action: str
    resource_id: str
    payload: dict[str, object]
    created_at: datetime


class InvestigationSummary(BaseModel):
    id: str
    case_id: str
    status: str
    risk_score: int
    severity: str
    created_at: datetime


class AgentStatus(BaseModel):
    id: str
    name: str
    category: str
    mode: str
    status: str
    supported_kinds: list[str]
    description: str


class PolicyDefinition(BaseModel):
    id: str
    name: str
    version: str
    enabled: bool
    threshold: int
    description: str


class ModelHealth(BaseModel):
    id: str
    name: str
    provider: str
    status: str
    latency_ms: int | None
    last_checked: datetime
    detail: str


class GraphNode(BaseModel):
    id: str
    label: str
    kind: str
    risk: int


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class EntityGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
