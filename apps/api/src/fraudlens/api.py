from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal, require_principal
from fraudlens.database import get_session
from fraudlens.dependencies import get_orchestrator
from fraudlens.domain.models import InvestigationReport, InvestigationRequest
from fraudlens.orchestrator import InvestigationOrchestrator
from fraudlens.schemas import (
    AgentStatus,
    AuditEntry,
    CaseCreate,
    CaseDetail,
    CaseSummary,
    DashboardMetrics,
    EntityGraph,
    EvidenceCreate,
    InvestigationSummary,
    ModelHealth,
    PolicyDefinition,
)
from fraudlens.services import (
    add_evidence,
    audit_log,
    create_case,
    dashboard,
    entity_graph,
    get_case_detail,
    investigate_case,
    list_cases,
    list_investigations,
)

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "fraudlens-api"}


@router.post("/investigations", response_model=InvestigationReport)
async def investigate(
    request: InvestigationRequest,
    orchestrator: Annotated[InvestigationOrchestrator, Depends(get_orchestrator)],
    _: Annotated[Principal, Depends(require_principal)],
) -> InvestigationReport:
    return await orchestrator.investigate(request)


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> DashboardMetrics:
    return await dashboard(session, principal)


@router.get("/cases", response_model=list[CaseSummary])
async def get_cases(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[CaseSummary]:
    return await list_cases(session, principal)


@router.post("/cases", response_model=CaseSummary, status_code=201)
async def post_case(
    payload: CaseCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> CaseSummary:
    return await create_case(session, principal, payload)


@router.get("/cases/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> CaseDetail:
    return await get_case_detail(session, principal, case_id)


@router.post("/cases/{case_id}/evidence", status_code=201)
async def post_evidence(
    case_id: str,
    payload: EvidenceCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    return await add_evidence(session, principal, case_id, payload)


@router.post("/cases/{case_id}/investigate", response_model=InvestigationReport)
async def run_case_investigation(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    orchestrator: Annotated[InvestigationOrchestrator, Depends(get_orchestrator)],
) -> InvestigationReport:
    return await investigate_case(session, principal, case_id, orchestrator)


@router.get("/audit", response_model=list[AuditEntry])
async def get_audit_log(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[AuditEntry]:
    return await audit_log(session, principal)


@router.get("/investigations", response_model=list[InvestigationSummary])
async def get_investigations(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[InvestigationSummary]:
    return await list_investigations(session, principal)


@router.get("/graph", response_model=EntityGraph)
async def get_entity_graph(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> EntityGraph:
    return await entity_graph(session, principal)


@router.get("/agents", response_model=list[AgentStatus])
async def get_agents(_: Annotated[Principal, Depends(require_principal)]) -> list[AgentStatus]:
    return [
        AgentStatus(
            id="email-security",
            name="Email Security",
            category="Communication",
            mode="Deterministic",
            status="ONLINE",
            supported_kinds=["email"],
            description="SPF, DKIM, DMARC and sender-path validation.",
        ),
        AgentStatus(
            id="document-integrity",
            name="Document Integrity",
            category="Documents",
            mode="Deterministic",
            status="ONLINE",
            supported_kinds=["document", "invoice"],
            description="Payment detail and document metadata consistency rules.",
        ),
        AgentStatus(
            id="url-reputation",
            name="URL Reputation",
            category="Network",
            mode="Deterministic",
            status="ONLINE",
            supported_kinds=["url"],
            description="Domain age and URL reputation indicators.",
        ),
        AgentStatus(
            id="ai-investigator",
            name="AI Investigator",
            category="Investigation",
            mode="LLM-assisted",
            status="STANDBY",
            supported_kinds=["finding"],
            description="Evidence-grounded narrative generation; cannot alter risk.",
        ),
    ]


@router.get("/policies", response_model=list[PolicyDefinition])
async def get_policies(
    _: Annotated[Principal, Depends(require_principal)],
) -> list[PolicyDefinition]:
    return [
        PolicyDefinition(
            id="critical-risk",
            name="Critical risk escalation",
            version="2026.08.1",
            enabled=True,
            threshold=80,
            description="Routes cases scoring 80 or above to immediate human review.",
        ),
        PolicyDefinition(
            id="email-auth",
            name="Email authentication",
            version="2026.08.1",
            enabled=True,
            threshold=60,
            description="Raises high-risk findings when SPF, DKIM, or DMARC fails.",
        ),
        PolicyDefinition(
            id="bank-change",
            name="Supplier bank change",
            version="2026.08.1",
            enabled=True,
            threshold=70,
            description="Escalates unverified IBAN changes on invoices.",
        ),
        PolicyDefinition(
            id="llm-citations",
            name="LLM citation coverage",
            version="2026.08.1",
            enabled=True,
            threshold=100,
            description="Requires every generated claim to reference validated evidence.",
        ),
    ]


@router.get("/models/health", response_model=list[ModelHealth])
async def get_model_health(
    _: Annotated[Principal, Depends(require_principal)],
) -> list[ModelHealth]:
    now = datetime.now(UTC)
    return [
        ModelHealth(
            id="rules-2026-08",
            name="Fraud Rules Engine",
            provider="FraudLens",
            status="HEALTHY",
            latency_ms=3,
            last_checked=now,
            detail="Ruleset 2026.08.1 loaded.",
        ),
        ModelHealth(
            id="openai-narrative",
            name="Investigation Narrative",
            provider="OpenAI / configurable",
            status="STANDBY",
            latency_ms=None,
            last_checked=now,
            detail="Enabled only when LLM_PROVIDER and credentials are configured.",
        ),
        ModelHealth(
            id="document-model",
            name="Document Vision",
            provider="Not configured",
            status="NOT_CONFIGURED",
            latency_ms=None,
            last_checked=now,
            detail="Awaiting a validated OCR/tamper model adapter.",
        ),
        ModelHealth(
            id="deepfake-model",
            name="Deepfake Detection",
            provider="Not configured",
            status="NOT_CONFIGURED",
            latency_ms=None,
            last_checked=now,
            detail="No production model has been approved or calibrated.",
        ),
    ]
