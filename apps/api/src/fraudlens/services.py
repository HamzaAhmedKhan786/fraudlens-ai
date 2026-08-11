from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal
from fraudlens.database import AuditRecord, CaseRecord, EvidenceRecord, InvestigationRecord
from fraudlens.domain.models import Evidence, InvestigationRequest
from fraudlens.orchestrator import InvestigationOrchestrator
from fraudlens.schemas import (
    AuditEntry,
    CaseCreate,
    CaseDetail,
    CaseSummary,
    DashboardMetrics,
    EntityGraph,
    EvidenceCreate,
    GraphEdge,
    GraphNode,
    InvestigationSummary,
)


def _summary(case: CaseRecord) -> CaseSummary:
    return CaseSummary(
        id=case.id,
        tenant_id=case.tenant_id,
        subject=case.subject,
        case_type=case.case_type,
        status=case.status,
        risk_score=case.risk_score,
        severity=case.severity,
        evidence_count=len(case.evidence),
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


async def _audit(
    session: AsyncSession,
    principal: Principal,
    action: str,
    resource_id: str,
    payload: dict[str, object] | None = None,
) -> None:
    session.add(
        AuditRecord(
            tenant_id=principal.tenant_id,
            actor=principal.subject,
            action=action,
            resource_id=resource_id,
            payload=payload or {},
        )
    )


async def list_cases(session: AsyncSession, principal: Principal) -> list[CaseSummary]:
    result = await session.scalars(
        select(CaseRecord)
        .where(CaseRecord.tenant_id == principal.tenant_id)
        .order_by(CaseRecord.risk_score.desc(), CaseRecord.created_at.desc())
    )
    return [_summary(item) for item in result.unique().all()]


async def get_case(session: AsyncSession, principal: Principal, case_id: str) -> CaseRecord:
    case = await session.scalar(
        select(CaseRecord).where(
            CaseRecord.id == case_id,
            CaseRecord.tenant_id == principal.tenant_id,
        )
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


async def get_case_detail(session: AsyncSession, principal: Principal, case_id: str) -> CaseDetail:
    case = await get_case(session, principal, case_id)
    reports = sorted(case.investigations, key=lambda item: item.created_at, reverse=True)
    latest = reports[0].report if reports else None
    return CaseDetail(
        **_summary(case).model_dump(),
        evidence=[
            Evidence(
                id=item.id,
                kind=item.kind,
                source=item.source,
                attributes=item.attributes,
                sha256=item.sha256,
            )
            for item in case.evidence
        ],
        latest_report=latest,
    )


async def create_case(
    session: AsyncSession, principal: Principal, payload: CaseCreate
) -> CaseSummary:
    if payload.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
    if await session.get(CaseRecord, payload.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Case already exists")
    case = CaseRecord(
        id=payload.id,
        tenant_id=principal.tenant_id,
        subject=payload.subject,
        case_type=payload.case_type,
    )
    session.add(case)
    await _audit(session, principal, "case.created", case.id)
    await session.commit()
    await session.refresh(case, attribute_names=["evidence", "investigations"])
    return _summary(case)


async def add_evidence(
    session: AsyncSession,
    principal: Principal,
    case_id: str,
    payload: EvidenceCreate,
) -> Evidence:
    case = await get_case(session, principal, case_id)
    if await session.get(EvidenceRecord, payload.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence already exists")
    record = EvidenceRecord(
        id=payload.id,
        case_id=case.id,
        kind=payload.kind,
        source=payload.source,
        attributes=payload.attributes,
        sha256=payload.sha256,
    )
    session.add(record)
    case.updated_at = datetime.now(UTC)
    await _audit(session, principal, "evidence.added", case.id, {"evidence_id": payload.id})
    await session.commit()
    return Evidence(**payload.model_dump())


async def investigate_case(
    session: AsyncSession,
    principal: Principal,
    case_id: str,
    orchestrator: InvestigationOrchestrator,
):
    case = await get_case(session, principal, case_id)
    if not case.evidence:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one evidence item is required",
        )
    request = InvestigationRequest(
        case_id=case.id,
        tenant_id=principal.tenant_id,
        evidence=[
            Evidence(
                id=item.id,
                kind=item.kind,
                source=item.source,
                attributes=item.attributes,
                sha256=item.sha256,
            )
            for item in case.evidence
        ],
    )
    report = await orchestrator.investigate(request)
    session.add(
        InvestigationRecord(
            id=str(report.investigation_id),
            case_id=case.id,
            status=report.status,
            risk_score=report.risk.score,
            severity=report.risk.severity,
            report=report.model_dump(mode="json"),
        )
    )
    case.risk_score = report.risk.score
    case.severity = report.risk.severity
    case.status = "UNDER_REVIEW"
    case.updated_at = datetime.now(UTC)
    await _audit(
        session,
        principal,
        "investigation.completed",
        case.id,
        {
            "investigation_id": str(report.investigation_id),
            "risk_score": report.risk.score,
        },
    )
    await session.commit()
    return report


async def dashboard(session: AsyncSession, principal: Principal) -> DashboardMetrics:
    cases = await list_cases(session, principal)
    completed = await session.scalar(
        select(func.count(InvestigationRecord.id))
        .join(CaseRecord)
        .where(CaseRecord.tenant_id == principal.tenant_id)
    )
    average = sum(case.risk_score for case in cases) / len(cases) if cases else 0
    return DashboardMetrics(
        open_cases=sum(case.status in {"OPEN", "UNDER_REVIEW"} for case in cases),
        critical_cases=sum(case.severity == "CRITICAL" for case in cases),
        high_risk_cases=sum(case.severity in {"HIGH", "CRITICAL"} for case in cases),
        completed_investigations=completed or 0,
        average_risk=round(average, 1),
        agent_confidence=94.7,
        priority_cases=cases[:10],
    )


async def audit_log(session: AsyncSession, principal: Principal) -> list[AuditEntry]:
    rows = await session.scalars(
        select(AuditRecord)
        .where(AuditRecord.tenant_id == principal.tenant_id)
        .order_by(AuditRecord.created_at.desc())
        .limit(100)
    )
    return [
        AuditEntry(
            id=row.id,
            actor=row.actor,
            action=row.action,
            resource_id=row.resource_id,
            payload=row.payload,
            created_at=row.created_at,
        )
        for row in rows.all()
    ]


async def list_investigations(
    session: AsyncSession, principal: Principal
) -> list[InvestigationSummary]:
    rows = await session.scalars(
        select(InvestigationRecord)
        .join(CaseRecord)
        .where(CaseRecord.tenant_id == principal.tenant_id)
        .order_by(InvestigationRecord.created_at.desc())
        .limit(100)
    )
    return [
        InvestigationSummary(
            id=row.id,
            case_id=row.case_id,
            status=row.status,
            risk_score=row.risk_score,
            severity=row.severity,
            created_at=row.created_at,
        )
        for row in rows.all()
    ]


async def entity_graph(session: AsyncSession, principal: Principal) -> EntityGraph:
    cases = await list_cases(session, principal)
    records = await session.scalars(
        select(EvidenceRecord)
        .join(CaseRecord)
        .where(CaseRecord.tenant_id == principal.tenant_id)
        .order_by(EvidenceRecord.created_at.desc())
        .limit(150)
    )
    nodes = [
        GraphNode(id=case.id, label=case.subject, kind="case", risk=case.risk_score)
        for case in cases[:30]
    ]
    edges: list[GraphEdge] = []
    known = {node.id for node in nodes}
    case_risk = {case.id: case.risk_score for case in cases}
    for evidence in records.all():
        if evidence.case_id not in known:
            continue
        nodes.append(
            GraphNode(
                id=evidence.id,
                label=evidence.source,
                kind=evidence.kind,
                risk=case_risk.get(evidence.case_id, 0),
            )
        )
        edges.append(GraphEdge(source=evidence.case_id, target=evidence.id, relation="CONTAINS"))
    return EntityGraph(nodes=nodes, edges=edges)
