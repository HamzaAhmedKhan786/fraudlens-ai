from datetime import datetime

from pydantic import BaseModel, Field

from fraudlens.domain.models import Evidence, InvestigationReport


class CaseCreate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,100}$")
    tenant_id: str = Field(default="demo", min_length=2, max_length=100)
    subject: str = Field(min_length=3, max_length=240)
    case_type: str = Field(min_length=2, max_length=80)
    analysis_modules: list[str] = Field(default_factory=list, max_length=20)
    evidence_sources: list[str] = Field(default_factory=list, max_length=10)


class CaseSummary(BaseModel):
    id: str
    tenant_id: str
    subject: str
    case_type: str
    analysis_modules: list[str]
    evidence_sources: list[str]
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


class ReviewRequestCreate(BaseModel):
    request_type: str = Field(pattern="^(VERIFICATION|FALSE_POSITIVE|REOPEN|ADDITIONAL_REVIEW)$")
    reason: str = Field(min_length=10, max_length=4000)


class ReviewDecision(BaseModel):
    action: str = Field(
        pattern="^(APPROVE_LEGITIMATE|CONFIRM_SUSPICIOUS|REJECT|REQUEST_EVIDENCE|ESCALATE|REOPEN)$"
    )
    reason: str = Field(min_length=10, max_length=4000)


class ReviewRequest(BaseModel):
    id: str
    case_id: str
    requester: str
    request_type: str
    reason: str
    status: str
    reviewer: str | None
    decision_reason: str | None
    created_at: datetime
    updated_at: datetime


class CaseComment(BaseModel):
    id: str
    author: str
    body: str
    created_at: datetime


class DashboardMetrics(BaseModel):
    data_source: str
    open_cases: int
    critical_cases: int
    high_risk_cases: int
    completed_investigations: int
    average_risk: float
    agent_confidence: float
    priority_cases: list[CaseSummary]
    detection_signals: list["DetectionSignal"]


class DetectionSignal(BaseModel):
    name: str
    count: int
    share: float


class EvidenceCreate(Evidence):
    pass


class DeleteRequest(BaseModel):
    reason: str = Field(min_length=10, max_length=2000)


class BulkEvidenceDelete(DeleteRequest):
    evidence_ids: list[str] = Field(min_length=1, max_length=100)


class DeletionResult(BaseModel):
    deleted_ids: list[str]
    recovery_until: datetime


class OrganizationCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,99}$")
    name: str = Field(min_length=2, max_length=240)
    account_type: str = Field(pattern="^(INDIVIDUAL|ORGANIZATION)$")
    owner_email: str = Field(min_length=3, max_length=320)


class Organization(BaseModel):
    id: str
    name: str
    account_type: str
    status: str


class WorkspaceSummary(BaseModel):
    id: str
    name: str
    account_type: str
    role: str
    status: str


class Member(BaseModel):
    id: str
    subject: str
    email: str
    role: str
    status: str


class InvitationCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: str = Field(pattern="^(admin|analyst|viewer|reviewer|executive)$")


class Invitation(BaseModel):
    id: str
    email: str
    role: str
    status: str
    expires_at: datetime
    acceptance_token: str | None = None


class InvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    email: str = Field(min_length=3, max_length=320)


class EntitlementStatus(BaseModel):
    plan_code: str
    subscription_status: str
    limits: dict[str, int]
    usage: dict[str, int]
    remaining: dict[str, int]


class SubscriptionSelection(BaseModel):
    plan_code: str = Field(pattern="^(individual|small|medium|enterprise)$")
    billing_interval: str = Field(pattern="^(monthly|annual)$")


class BillingAction(BaseModel):
    url: str | None
    configured: bool
    detail: str


class ProviderCapability(BaseModel):
    provider: str
    status: str
    modes: list[str]
    detail: str


class AddinIngestRequest(BaseModel):
    provider: str = Field(pattern="^(gmail|microsoft)$")
    case_id: str = Field(min_length=3, max_length=100)
    internet_message_id: str = Field(min_length=3, max_length=998)
    consent_confirmed: bool


class SimilarityMatch(BaseModel):
    case_id: str
    subject: str
    similarity: float
    rationale: list[str]


class ChatPrompt(BaseModel):
    content: str = Field(min_length=2, max_length=4000)


class GuidePrompt(ChatPrompt):
    current_path: str | None = Field(default=None, max_length=200, pattern=r"^/[a-zA-Z0-9/_-]*$")


class GuideFeedback(BaseModel):
    helpful: bool
    document_ids: list[str] = Field(default_factory=list, max_length=10)
    revisions: list[str] = Field(default_factory=list, max_length=10)


class GuideResponse(BaseModel):
    content: str
    model: str
    suggested_path: str | None = None
    citations: list[dict[str, str]] = Field(default_factory=list)


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    citations: list[str]
    model: str
    created_at: datetime


class ChatFeedbackCreate(BaseModel):
    rating: str = Field(pattern="^(CORRECT|INCORRECT|FALSE_POSITIVE|MISSING_EVIDENCE|OTHER)$")
    explanation: str | None = Field(default=None, max_length=4000)


class ChatFeedback(BaseModel):
    id: str
    message_id: str
    rating: str
    explanation: str | None
    reviewed: bool
    created_at: datetime


class EvaluationPromotion(BaseModel):
    expected_assessment: str = Field(min_length=10, max_length=4000)


class EvaluationExample(BaseModel):
    id: str
    case_id: str
    message_id: str
    feedback_id: str
    expected_assessment: str
    approved_by: str
    created_at: datetime


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


class DomainLookup(BaseModel):
    domain: str = Field(min_length=3, max_length=253, pattern=r"^[A-Za-z0-9.-]+$")


class PublicIntelligence(BaseModel):
    id: str
    indicator_type: str
    indicator: str
    provider: str
    source_uri: str
    status: str
    facts: dict[str, object]
    fetched_at: datetime


class GmailAuthorization(BaseModel):
    authorization_url: str


class GmailConnection(BaseModel):
    connected: bool
    email_address: str | None = None
    status: str
    scopes: list[str] = Field(default_factory=list)
    connected_at: datetime | None = None
    last_sync_at: datetime | None = None
    last_error: str | None = None


class GmailSyncRequest(BaseModel):
    case_id: str = Field(min_length=3, max_length=100)
    label_ids: list[str] = Field(default_factory=list, max_length=20)
    sender: str | None = Field(default=None, max_length=320)
    after: str | None = Field(default=None, pattern=r"^\d{4}/\d{2}/\d{2}$")
    before: str | None = Field(default=None, pattern=r"^\d{4}/\d{2}/\d{2}$")
    has_attachment: bool | None = None
    max_messages: int = Field(default=25, ge=1, le=100)
    page_token: str | None = Field(default=None, max_length=2048)


class GmailSyncResult(BaseModel):
    imported_messages: int
    imported_attachments: int
    duplicate_messages: int
    failed_messages: list[dict[str, str]]
    next_page_token: str | None = None
