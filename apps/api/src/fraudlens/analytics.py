"""Bounded read models for the enterprise console; never hydrate full case relationships."""

from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal
from fraudlens.database import (
    AuditRecord,
    CaseRecord,
    EvidenceRecord,
    InvestigationRecord,
    ReviewRequestRecord,
    UploadRecord,
    WorkspaceSettingsRecord,
)


def visible_cases(principal: Principal):
    return (CaseRecord.tenant_id == principal.tenant_id, CaseRecord.deleted_at.is_(None))


async def search_cases(
    session: AsyncSession,
    principal: Principal,
    query: str = "",
    severity: str | None = None,
    status: str | None = None,
    sort: Literal["updated", "risk", "created", "subject"] = "updated",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    filters = list(visible_cases(principal))
    if query:
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        filters.append(
            CaseRecord.id.ilike(pattern, escape="\\")
            | CaseRecord.subject.ilike(pattern, escape="\\")
            | CaseRecord.case_type.ilike(pattern, escape="\\")
        )
    if severity:
        filters.append(CaseRecord.severity == severity)
    if status:
        filters.append(CaseRecord.status == status)
    total = await session.scalar(select(func.count()).select_from(CaseRecord).where(*filters))
    evidence_count = (
        select(func.count(EvidenceRecord.id))
        .where(EvidenceRecord.case_id == CaseRecord.id, EvidenceRecord.deleted_at.is_(None))
        .correlate(CaseRecord)
        .scalar_subquery()
    )
    order = {
        "updated": CaseRecord.updated_at.desc(),
        "risk": CaseRecord.risk_score.desc(),
        "created": CaseRecord.created_at.desc(),
        "subject": CaseRecord.subject.asc(),
    }[sort]
    rows = (
        (
            await session.execute(
                select(
                    CaseRecord.id,
                    CaseRecord.subject,
                    CaseRecord.case_type,
                    CaseRecord.status,
                    CaseRecord.risk_score,
                    CaseRecord.severity,
                    CaseRecord.assignee,
                    CaseRecord.updated_at,
                    evidence_count.label("evidence_count"),
                )
                .where(*filters)
                .order_by(order, CaseRecord.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .mappings()
        .all()
    )
    return {
        "items": [dict(row) for row in rows],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }


async def overview(session: AsyncSession, principal: Principal, days: int) -> dict:
    now = datetime.now(UTC)
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    filters = visible_cases(principal)
    totals = (
        (
            await session.execute(
                select(
                    func.count().label("total_cases"),
                    func.coalesce(
                        func.sum(
                            case(
                                (CaseRecord.status.in_(["OPEN", "UNDER_REVIEW", "ESCALATED"]), 1),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("open_cases"),
                    func.coalesce(
                        func.sum(case((CaseRecord.severity.in_(["HIGH", "CRITICAL"]), 1), else_=0)),
                        0,
                    ).label("high_risk_cases"),
                    func.coalesce(func.avg(CaseRecord.risk_score), 0).label("average_risk"),
                ).where(*filters)
            )
        )
        .mappings()
        .one()
    )
    distribution = (
        (
            await session.execute(
                select(CaseRecord.severity, func.count().label("count"))
                .where(*filters)
                .group_by(CaseRecord.severity)
            )
        )
        .mappings()
        .all()
    )
    investigation_total = await session.scalar(
        select(func.count(InvestigationRecord.id)).join(CaseRecord).where(*filters)
    )
    upload_filters = (*filters, UploadRecord.tenant_id == principal.tenant_id)
    processed_total = await session.scalar(
        select(func.count(UploadRecord.id))
        .join(CaseRecord)
        .where(*upload_filters, UploadRecord.status == "PROCESSED")
    )
    processing = (
        (
            await session.execute(
                select(UploadRecord.status, func.count().label("count"))
                .join(CaseRecord)
                .where(*upload_filters)
                .group_by(UploadRecord.status)
            )
        )
        .mappings()
        .all()
    )
    pending = await session.scalar(
        select(func.count(ReviewRequestRecord.id))
        .join(CaseRecord)
        .where(
            *filters,
            ReviewRequestRecord.tenant_id == principal.tenant_id,
            ReviewRequestRecord.status == "PENDING",
        )
    )
    daily = {
        (start + timedelta(days=i)).date().isoformat(): {
            "date": (start + timedelta(days=i)).date().isoformat(),
            "created": 0,
            "completed": 0,
            "high_risk": 0,
            "evidence": 0,
        }
        for i in range(days)
    }
    groups = [
        (
            "created",
            select(func.date(CaseRecord.created_at), func.count())
            .where(*filters, CaseRecord.created_at >= start)
            .group_by(func.date(CaseRecord.created_at)),
        ),
        (
            "completed",
            select(func.date(InvestigationRecord.created_at), func.count())
            .join(CaseRecord)
            .where(
                *filters,
                InvestigationRecord.created_at >= start,
                InvestigationRecord.status == "COMPLETED",
            )
            .group_by(func.date(InvestigationRecord.created_at)),
        ),
        (
            "high_risk",
            select(func.date(InvestigationRecord.created_at), func.count())
            .join(CaseRecord)
            .where(
                *filters,
                InvestigationRecord.created_at >= start,
                InvestigationRecord.severity.in_(["HIGH", "CRITICAL"]),
            )
            .group_by(func.date(InvestigationRecord.created_at)),
        ),
        (
            "evidence",
            select(func.date(UploadRecord.updated_at), func.count())
            .join(CaseRecord)
            .where(
                *upload_filters,
                UploadRecord.updated_at >= start,
                UploadRecord.status == "PROCESSED",
            )
            .group_by(func.date(UploadRecord.updated_at)),
        ),
    ]
    for key, statement in groups:
        for day, count in await session.execute(statement):
            if str(day) in daily:
                daily[str(day)][key] = count
    latest = (
        (
            await session.execute(
                select(
                    InvestigationRecord.report,
                    CaseRecord.id,
                    CaseRecord.subject,
                    CaseRecord.status,
                    CaseRecord.disposition,
                )
                .join(CaseRecord)
                .where(*filters)
                .order_by(InvestigationRecord.created_at.desc())
                .limit(1)
            )
        )
        .mappings()
        .first()
    )
    activity = (
        (
            await session.execute(
                select(
                    AuditRecord.id,
                    AuditRecord.action,
                    AuditRecord.resource_id,
                    AuditRecord.created_at,
                    AuditRecord.actor,
                )
                .where(AuditRecord.tenant_id == principal.tenant_id)
                .order_by(AuditRecord.created_at.desc())
                .limit(6)
            )
        )
        .mappings()
        .all()
    )
    categories = (
        (
            await session.execute(
                select(CaseRecord.case_type.label("name"), func.count().label("count"))
                .where(*filters)
                .group_by(CaseRecord.case_type)
                .order_by(func.count().desc())
                .limit(5)
            )
        )
        .mappings()
        .all()
    )
    threshold = await session.scalar(
        select(WorkspaceSettingsRecord.critical_risk_threshold).where(
            WorkspaceSettingsRecord.tenant_id == principal.tenant_id
        )
    )
    return {
        "data_source": "DEMO_DATASET" if principal.tenant_id == "demo" else "OPERATIONAL_DATA",
        "as_of": now,
        "days": days,
        "summary": {
            **dict(totals),
            "average_risk": round(totals["average_risk"], 1),
            "total_investigations": investigation_total or 0,
            "evidence_processed": processed_total or 0,
            "pending_reviews": pending or 0,
        },
        "distribution": [dict(row) for row in distribution],
        "trend": list(daily.values()),
        "processing": [dict(row) for row in processing],
        "categories": [dict(row) for row in categories],
        "latest": dict(latest) if latest else None,
        "activity": [dict(row) for row in activity],
        "critical_threshold": threshold if threshold is not None else 80,
        "geography": {
            "available": False,
            "reason": "Verified country and location data is not available for these cases.",
        },
    }
