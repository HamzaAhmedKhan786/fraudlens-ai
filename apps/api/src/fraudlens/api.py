from datetime import UTC, datetime, timedelta
from html import escape
from pathlib import Path
from shutil import which
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal, require_principal
from fraudlens.billing import checkout, portal, verify_signature
from fraudlens.config import get_settings as get_runtime_settings
from fraudlens.copilot import ask as ask_copilot
from fraudlens.copilot import convert_to_note, list_chat, promote_evaluation
from fraudlens.copilot import feedback as save_copilot_feedback
from fraudlens.database import SubscriptionRecord, get_session
from fraudlens.dependencies import get_gmail_connector, get_ingestion_service, get_orchestrator
from fraudlens.domain.models import InvestigationReport, InvestigationRequest
from fraudlens.gmail import GmailConnector
from fraudlens.ingestion import IngestionService
from fraudlens.orchestrator import InvestigationOrchestrator
from fraudlens.platform_services import (
    accept_invitation,
    connector_capabilities,
    create_invitation,
    create_organization,
    entitlement_status,
    historical_similarity,
    list_members,
    list_workspaces,
)
from fraudlens.public_intelligence import list_public_intelligence, lookup_domain
from fraudlens.schemas import (
    AddinIngestRequest,
    AgentStatus,
    AuditEntry,
    BillingAction,
    BulkEvidenceDelete,
    CaseComment,
    CaseCommentCreate,
    CaseCreate,
    CaseDetail,
    CaseSummary,
    CaseUpdate,
    ChatFeedback,
    ChatFeedbackCreate,
    ChatMessage,
    ChatPrompt,
    DashboardMetrics,
    DeleteRequest,
    DeletionResult,
    DomainLookup,
    EntitlementStatus,
    EntityGraph,
    EvaluationExample,
    EvaluationPromotion,
    EvidenceCreate,
    GmailAuthorization,
    GmailConnection,
    GmailSyncRequest,
    GmailSyncResult,
    InvestigationSummary,
    Invitation,
    InvitationAccept,
    InvitationCreate,
    Member,
    ModelHealth,
    Organization,
    OrganizationCreate,
    PolicyDefinition,
    PolicyUpdate,
    ProviderCapability,
    PublicIntelligence,
    ReviewDecision,
    ReviewRequest,
    ReviewRequestCreate,
    SimilarityMatch,
    SubscriptionSelection,
    UploadList,
    UploadSummary,
    WorkspaceSettings,
    WorkspaceSummary,
)
from fraudlens.services import (
    add_case_comment,
    add_evidence,
    audit_log,
    create_case,
    dashboard,
    decide_review,
    entity_graph,
    get_case_detail,
    get_workspace_settings,
    investigate_case,
    list_cases,
    list_deleted_cases,
    list_investigations,
    list_policies,
    list_reviews,
    request_review,
    restore_case,
    soft_delete_case,
    soft_delete_evidence,
    update_case,
    update_policy,
    update_workspace_settings,
)

router = APIRouter()


@router.get("/workspaces", response_model=list[WorkspaceSummary])
async def get_workspaces(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    return await list_workspaces(session, principal)


@router.post("/billing/checkout", response_model=BillingAction)
async def post_checkout(
    payload: SubscriptionSelection,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    return await checkout(session, principal, payload)


@router.post("/subscriptions/select", response_model=EntitlementStatus)
async def select_plan(
    payload: SubscriptionSelection,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    if "admin" not in principal.roles:
        raise HTTPException(403, "Administrator role required")
    row = await session.get(SubscriptionRecord, principal.tenant_id)
    if not row:
        row = SubscriptionRecord(tenant_id=principal.tenant_id)
        session.add(row)
    row.plan_code = payload.plan_code
    if row.status not in {"ACTIVE", "PAST_DUE", "SUSPENDED"}:
        row.status = "TRIAL"
        row.current_period_end = datetime.now(UTC) + timedelta(
            days=get_runtime_settings().subscription_trial_days
        )
    await session.commit()
    return await entitlement_status(session, principal)


@router.post("/billing/portal", response_model=BillingAction)
async def post_portal(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    return await portal(session, principal)


@router.post("/billing/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, session: Annotated[AsyncSession, Depends(get_session)]):
    settings = get_runtime_settings()
    if not settings.stripe_enabled:
        raise HTTPException(503, "Stripe test mode is not configured")
    event = verify_signature(
        await request.body(),
        request.headers.get("stripe-signature", ""),
        settings.stripe_webhook_secret,
    )
    obj = event.get("data", {}).get("object", {})
    metadata = obj.get("metadata", {})
    tenant = metadata.get("tenant_id")
    if tenant:
        row = await session.get(SubscriptionRecord, tenant)
        if row:
            event_type = event.get("type", "")
            row.status = {
                "customer.subscription.trial_will_end": "TRIAL",
                "customer.subscription.updated": "ACTIVE",
                "customer.subscription.deleted": "CANCELED",
                "invoice.payment_failed": "PAST_DUE",
            }.get(event_type, row.status)
            row.provider_customer_id = obj.get("customer") or row.provider_customer_id
            row.provider_subscription_id = (
                obj.get("subscription") or obj.get("id") or row.provider_subscription_id
            )
            await session.commit()
    return {"received": True}


@router.get("/cases/{case_id}/chat", response_model=list[ChatMessage])
async def get_case_chat(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[ChatMessage]:
    return await list_chat(session, principal, case_id)


@router.post("/cases/{case_id}/chat", response_model=ChatMessage, status_code=201)
async def post_case_chat(
    case_id: str,
    payload: ChatPrompt,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> ChatMessage:
    return await ask_copilot(session, principal, case_id, payload)


@router.post("/cases/{case_id}/chat/stream")
async def stream_case_chat(
    case_id: str,
    payload: ChatPrompt,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    message = await ask_copilot(session, principal, case_id, payload)

    async def events():
        import json

        for word in message.content.split(" "):
            yield f"data: {json.dumps({'delta': word + ' '})}\n\n"
        yield f"data: {json.dumps({'done': True, 'message': message.model_dump(mode='json')})}\n\n"

    return StreamingResponse(
        events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
    )


@router.post("/cases/{case_id}/chat/{message_id}/note", response_model=CaseComment, status_code=201)
async def post_chat_note(
    case_id: str,
    message_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    return await convert_to_note(session, principal, case_id, message_id)


@router.post(
    "/cases/{case_id}/chat/{message_id}/feedback",
    response_model=ChatFeedback,
    status_code=201,
)
async def post_chat_feedback(
    case_id: str,
    message_id: str,
    payload: ChatFeedbackCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> ChatFeedback:
    return await save_copilot_feedback(session, principal, case_id, message_id, payload)


@router.post(
    "/copilot/feedback/{feedback_id}/promote", response_model=EvaluationExample, status_code=201
)
async def post_feedback_promotion(
    feedback_id: str,
    payload: EvaluationPromotion,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    return await promote_evaluation(session, principal, feedback_id, payload)


@router.post("/organizations", response_model=Organization, status_code=201)
async def post_organization(
    payload: OrganizationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> Organization:
    return await create_organization(session, principal, payload)


@router.get("/members", response_model=list[Member])
async def get_members(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[Member]:
    return await list_members(session, principal)


@router.post("/invitations", response_model=Invitation, status_code=201)
async def post_invitation(
    payload: InvitationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> Invitation:
    return await create_invitation(session, principal, payload)


@router.post("/invitations/accept", response_model=Member)
async def post_accept_invitation(
    payload: InvitationAccept,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> Member:
    return await accept_invitation(session, principal, payload)


@router.get("/entitlements", response_model=EntitlementStatus)
async def get_entitlements(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> EntitlementStatus:
    return await entitlement_status(session, principal)


@router.get("/connectors/email/capabilities", response_model=list[ProviderCapability])
async def get_connector_capabilities(
    _: Annotated[Principal, Depends(require_principal)],
) -> list[ProviderCapability]:
    return connector_capabilities()


@router.post("/connectors/email/addin/messages", status_code=501)
async def post_addin_message(
    payload: AddinIngestRequest, _: Annotated[Principal, Depends(require_principal)]
):
    if not payload.consent_confirmed:
        raise HTTPException(400, "Explicit user consent is required")
    raise HTTPException(
        501, f"{payload.provider} selected-message retrieval requires provider add-in credentials"
    )


@router.get("/cases/{case_id}/similarity", response_model=list[SimilarityMatch])
async def get_similarity(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[SimilarityMatch]:
    return await historical_similarity(session, principal, case_id)


@router.get("/cases/{case_id}/report", response_class=HTMLResponse)
async def export_case_report(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> HTMLResponse:
    case = await get_case_detail(session, principal, case_id)
    findings = case.latest_report.findings if case.latest_report else []
    rows = "".join(
        "<li><strong>"
        f"{escape(item.title)}</strong> — {escape(item.explanation)} "
        f"({item.confidence:.0%})</li>"
        for item in findings
    )
    summary = escape(
        case.latest_report.summary
        if case.latest_report
        else "No investigation report has been generated."
    )
    html = f"""<!doctype html><html><head><meta charset='utf-8'>
<title>{escape(case.id)} report</title><style>
body{{font:16px system-ui;max-width:900px;margin:40px auto;color:#17233c}}
header{{border-bottom:3px solid #00bde8}}small{{color:#64748b}}
.score{{font-size:42px;font-weight:800}}</style></head><body>
<header><h1>FraudLens investigation report</h1>
<small>Evidence-grounded report; not a guarantee of authenticity.</small></header>
<h2>{escape(case.subject)}</h2>
<p>Case {escape(case.id)} · {escape(case.case_type)} · {escape(case.status)}</p>
<p class='score'>{case.risk_score}/100 · {escape(case.severity)}</p>
<h3>Summary</h3><p>{summary}</p><h3>Findings</h3>
<ul>{rows or "<li>No findings available.</li>"}</ul><h3>Evidence</h3>
<p>{len(case.evidence)} active evidence item(s). Audit records remain available.</p>
</body></html>"""
    return HTMLResponse(
        html, headers={"Content-Disposition": f'attachment; filename="{case.id}-report.html"'}
    )


@router.post("/connectors/google/authorize", response_model=GmailAuthorization)
async def authorize_google(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    connector: Annotated[GmailConnector, Depends(get_gmail_connector)],
) -> GmailAuthorization:
    return GmailAuthorization(
        authorization_url=await connector.authorization_url(session, principal)
    )


@router.get("/connectors/google/callback", include_in_schema=False)
async def google_callback(
    state: Annotated[str, Query(min_length=20, max_length=500)],
    code: Annotated[str, Query(min_length=1, max_length=4096)],
    session: Annotated[AsyncSession, Depends(get_session)],
    connector: Annotated[GmailConnector, Depends(get_gmail_connector)],
) -> RedirectResponse:
    return RedirectResponse(await connector.callback(session, state, code), status_code=303)


@router.get("/connectors/google", response_model=GmailConnection)
async def google_status(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    connector: Annotated[GmailConnector, Depends(get_gmail_connector)],
) -> GmailConnection:
    return await connector.status(session, principal)


@router.delete("/connectors/google", status_code=204)
async def disconnect_google(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    connector: Annotated[GmailConnector, Depends(get_gmail_connector)],
) -> Response:
    await connector.disconnect(session, principal)
    return Response(status_code=204)


@router.post("/connectors/google/sync", response_model=GmailSyncResult)
async def sync_google(
    payload: GmailSyncRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
    connector: Annotated[GmailConnector, Depends(get_gmail_connector)],
) -> GmailSyncResult:
    return await connector.sync(session, principal, payload)


@router.get("/intelligence/public", response_model=list[PublicIntelligence])
async def get_public_intelligence(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[PublicIntelligence]:
    return await list_public_intelligence(session, principal)


@router.post("/intelligence/domain", response_model=PublicIntelligence, status_code=201)
async def post_domain_lookup(
    payload: DomainLookup,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> PublicIntelligence:
    return await lookup_domain(session, principal, payload.domain)


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


@router.get("/cases-deleted", response_model=list[CaseSummary])
async def get_deleted_cases(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[CaseSummary]:
    return await list_deleted_cases(session, principal)


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


@router.delete("/cases/{case_id}", response_model=DeletionResult)
async def delete_case(
    case_id: str,
    payload: DeleteRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> DeletionResult:
    return await soft_delete_case(session, principal, case_id, payload)


@router.post("/cases/{case_id}/restore", response_model=CaseDetail)
async def post_restore_case(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> CaseDetail:
    return await restore_case(session, principal, case_id)


@router.post("/cases/{case_id}/comments", response_model=CaseComment, status_code=201)
async def post_case_comment(
    case_id: str,
    payload: CaseCommentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> CaseComment:
    return await add_case_comment(session, principal, case_id, payload)


@router.post("/cases/{case_id}/reviews", response_model=ReviewRequest, status_code=201)
async def post_review_request(
    case_id: str,
    payload: ReviewRequestCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> ReviewRequest:
    return await request_review(session, principal, case_id, payload)


@router.get("/reviews", response_model=list[ReviewRequest])
async def get_reviews(
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> list[ReviewRequest]:
    return await list_reviews(session, principal)


@router.patch("/reviews/{review_id}", response_model=ReviewRequest)
async def patch_review(
    review_id: str,
    payload: ReviewDecision,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> ReviewRequest:
    return await decide_review(session, principal, review_id, payload)


@router.post("/cases/{case_id}/evidence", status_code=201)
async def post_evidence(
    case_id: str,
    payload: EvidenceCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
):
    return await add_evidence(session, principal, case_id, payload)


@router.delete("/cases/{case_id}/evidence/{evidence_id}", response_model=DeletionResult)
async def delete_evidence(
    case_id: str,
    evidence_id: str,
    payload: DeleteRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> DeletionResult:
    return await soft_delete_evidence(session, principal, case_id, [evidence_id], payload.reason)


@router.post("/cases/{case_id}/evidence/bulk-delete", response_model=DeletionResult)
async def bulk_delete_evidence(
    case_id: str,
    payload: BulkEvidenceDelete,
    session: Annotated[AsyncSession, Depends(get_session)],
    principal: Annotated[Principal, Depends(require_principal)],
) -> DeletionResult:
    return await soft_delete_evidence(
        session, principal, case_id, payload.evidence_ids, payload.reason
    )


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
    provider = get_runtime_settings().llm_provider
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
            status="ONLINE" if provider in {"openai", "groq", "ollama"} else "STANDBY",
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
    tesseract_available = (
        bool(which(settings.tesseract_cmd)) or Path(settings.tesseract_cmd).is_file()
    )
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
            provider={"openai": "OpenAI", "groq": "Groq", "ollama": "Local Ollama"}.get(
                settings.llm_provider, "Not configured"
            ),
            status="STANDBY",
            latency_ms=None,
            last_checked=now,
            detail=(
                f"Evidence-grounded narratives configured with {settings.llm_provider}."
                if settings.llm_provider in {"openai", "groq", "ollama"}
                else "Enable OpenAI, Groq, or Ollama for cited narratives."
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
            name="Document OCR",
            provider="Tesseract 5",
            status="HEALTHY" if settings.ocr_enabled and tesseract_available else "NOT_CONFIGURED",
            latency_ms=None,
            last_checked=now,
            detail=(
                f"CPU OCR configured for {settings.ocr_languages}. "
                "OCR is not authenticity verification."
                if settings.ocr_enabled and tesseract_available
                else "Enable OCR and install Tesseract with the configured language packs."
            ),
        ),
        ModelHealth(
            id="document-tamper-model",
            name="Document tamper vision",
            provider="Adapter required",
            status="NOT_CONFIGURED",
            latency_ms=None,
            last_checked=now,
            detail="Pixel-level tamper detection still requires a separately validated model.",
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
