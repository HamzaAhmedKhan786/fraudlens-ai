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
    assignee: str | None
    disposition: str | None
    evidence_count: int
    created_at: datetime
    updated_at: datetime


class CaseDetail(CaseSummary):
    evidence: list[Evidence]
    comments: list["CaseComment"]
    latest_report: InvestigationReport | None = None


class CaseUpdate(BaseModel):
    assignee: str | None = Field(default=None, max_length=160)
    status: str | None = Field(default=None, pattern="^(OPEN|UNDER_REVIEW|ESCALATED|RESOLVED)$")
    disposition: str | None = Field(
        default=None, pattern="^(CONFIRMED_FRAUD|FALSE_POSITIVE|INCONCLUSIVE)$"
    )


class CaseCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class CaseComment(BaseModel):
    id: str
    author: str
    body: str
    created_at: datetime


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


class PolicyUpdate(BaseModel):
    enabled: bool
    threshold: int = Field(ge=0, le=100)


class WorkspaceSettings(BaseModel):
    mandatory_human_review: bool = True
    llm_narrative_enabled: bool = False
    critical_risk_threshold: int = Field(default=80, ge=0, le=100)
    evidence_retention_days: int = Field(default=180, ge=1, le=3650)
    updated_at: datetime | None = None


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


class UploadSummary(BaseModel):
    id: str
    case_id: str
    filename: str
    declared_content_type: str | None
    detected_content_type: str
    size_bytes: int
    sha256: str
    status: str
    scan_status: str
    processing_attempts: int
    extracted: dict[str, object]
    error: str | None
    object_available: bool
    retention_expires_at: datetime
    metadata_expires_at: datetime
    created_at: datetime
    updated_at: datetime


class UploadList(BaseModel):
    items: list[UploadSummary]
    total: int
