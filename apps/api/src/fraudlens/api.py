from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal, require_principal
from fraudlens.config import get_settings as get_runtime_settings
from fraudlens.database import get_session
from fraudlens.dependencies import get_ingestion_service, get_orchestrator
from fraudlens.domain.models import InvestigationReport, InvestigationRequest
from fraudlens.ingestion import IngestionService
from fraudlens.orchestrator import InvestigationOrchestrator
from fraudlens.schemas import (
    AgentStatus,
    AuditEntry,
    CaseComment,
    CaseCommentCreate,
    CaseCreate,
    CaseDetail,
    CaseSummary,
    CaseUpdate,
    DashboardMetrics,
    EntityGraph,
    EvidenceCreate,
    InvestigationSummary,
    ModelHealth,
    PolicyDefinition,
    PolicyUpdate,
    UploadList,
    UploadSummary,
    WorkspaceSettings,
)
from fraudlens.services import (
    add_case_comment,
    add_evidence,
    audit_log,
    create_case,
    dashboard,
    entity_graph,
    get_case_detail,
    get_workspace_settings,
    investigate_case,
    list_cases,
    list_investigations,
    list_policies,
    update_case,
    update_policy,
    update_workspace_settings,
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


@router.patch("/cases/{case_id}", response_model=CaseDetail)
async def patch_case(
    case_id: str,
    payload: CaseUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> CaseDetail:
    return await update_case(session, principal, case_id, payload)


@router.post("/cases/{case_id}/comments", response_model=CaseComment, status_code=201)
async def post_case_comment(
    case_id: str,
    payload: CaseCommentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> CaseComment:
    return await add_case_comment(session, principal, case_id, payload)


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
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[PolicyDefinition]:
    return await list_policies(session, principal)


@router.put("/policies/{policy_id}", response_model=PolicyDefinition)
async def put_policy(
    policy_id: str,
    payload: PolicyUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> PolicyDefinition:
    return await update_policy(session, principal, policy_id, payload)


@router.get("/settings", response_model=WorkspaceSettings)
async def get_settings(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> WorkspaceSettings:
    return await get_workspace_settings(session, principal)


@router.put("/settings", response_model=WorkspaceSettings)
async def put_settings(
    payload: WorkspaceSettings,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> WorkspaceSettings:
    return await update_workspace_settings(session, principal, payload)


@router.get("/models/health", response_model=list[ModelHealth])
async def get_model_health(
    _: Annotated[Principal, Depends(require_principal)],
) -> list[ModelHealth]:
    now = datetime.now(UTC)
    settings = get_runtime_settings()
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
            id="llm-narrative",
            name="Investigation Narrative",
            provider={"openai": "OpenAI", "groq": "Groq"}.get(
                settings.llm_provider, "Not configured"
            ),
            status="STANDBY",
            latency_ms=None,
            last_checked=now,
            detail=(
                f"Evidence-grounded narratives configured with {settings.llm_provider}."
                if settings.llm_provider in {"openai", "groq"}
                else "Enable OpenAI or Groq with provider credentials for cited narratives."
            ),
        ),
        ModelHealth(
            id="document-extraction",
            name="Document extraction",
            provider="FraudLens deterministic parser",
            status="HEALTHY",
            latency_ms=8,
            last_checked=now,
            detail="PDF, DOCX and text extraction with IBAN and payment-change indicators.",
        ),
        ModelHealth(
            id="document-vision-model",
            name="Document OCR & tamper vision",
            provider="Adapter required",
            status="NOT_CONFIGURED",
            latency_ms=None,
            last_checked=now,
            detail="Scanned-image OCR and pixel-level tamper detection require a validated model.",
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
        ModelHealth(
            id="malware-scanner",
            name="Malware scanning",
            provider="ClamAV" if settings.clamav_enabled else "Not configured",
            status="HEALTHY" if settings.clamav_enabled else "NOT_CONFIGURED",
            latency_ms=None,
            last_checked=now,
            detail=(
                "Uploads are scanned before parsing; infected objects are quarantined."
                if settings.clamav_enabled
                else "Enable CLAMAV_ENABLED to scan uploads and quarantine infected evidence."
            ),
        ),
    ]


@router.post("/cases/{case_id}/uploads", response_model=UploadSummary, status_code=201)
async def upload_evidence(
    case_id: str,
    file: Annotated[UploadFile, File()],
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    ingestion: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> UploadSummary:
    return await ingestion.ingest(session, principal, case_id, file)


@router.get("/uploads", response_model=UploadList)
async def get_uploads(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    ingestion: Annotated[IngestionService, Depends(get_ingestion_service)],
    case_id: Annotated[str | None, Query(max_length=100)] = None,
) -> UploadList:
    return await ingestion.list(session, principal, case_id)


@router.get("/uploads/{upload_id}", response_model=UploadSummary)
async def get_upload(
    upload_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    ingestion: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> UploadSummary:
    return await ingestion.get(session, principal, upload_id)


@router.get("/uploads/{upload_id}/content")
async def download_upload(
    upload_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    ingestion: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> Response:
    data, record = await ingestion.download(session, principal, upload_id)
    safe_name = record.filename.replace('"', "")
    return Response(
        content=data,
        media_type=record.detected_content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/uploads/{upload_id}/retry", response_model=UploadSummary)
async def retry_upload(
    upload_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    ingestion: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> UploadSummary:
    return await ingestion.process(session, principal, upload_id)
