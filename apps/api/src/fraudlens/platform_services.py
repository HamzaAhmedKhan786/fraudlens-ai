import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal, require_role
from fraudlens.database import (
    AuditRecord,
    CaseRecord,
    InvitationRecord,
    MembershipRecord,
    OrganizationRecord,
    SubscriptionRecord,
    UsageLedgerRecord,
)
from fraudlens.schemas import (
    EntitlementStatus,
    Invitation,
    InvitationAccept,
    InvitationCreate,
    Member,
    Organization,
    OrganizationCreate,
    ProviderCapability,
    SimilarityMatch,
    WorkspaceSummary,
)

PLAN_LIMITS = {
    "individual": {
        "investigations": 25,
        "email_messages": 100,
        "ocr_pages": 100,
        "storage_mb": 1024,
        "gpu_seconds": 0,
    },
    "small": {
        "investigations": 250,
        "email_messages": 2500,
        "ocr_pages": 2000,
        "storage_mb": 10240,
        "gpu_seconds": 300,
    },
    "medium": {
        "investigations": 2500,
        "email_messages": 25000,
        "ocr_pages": 20000,
        "storage_mb": 102400,
        "gpu_seconds": 3600,
    },
    "enterprise": {
        "investigations": 100000,
        "email_messages": 1000000,
        "ocr_pages": 1000000,
        "storage_mb": 1048576,
        "gpu_seconds": 100000,
    },
}


async def create_organization(
    session: AsyncSession, principal: Principal, payload: OrganizationCreate
) -> Organization:
    require_role(principal, "admin")
    row = await session.get(OrganizationRecord, payload.id)
    if row:
        raise HTTPException(409, "Organization already exists")
    row = OrganizationRecord(id=payload.id, name=payload.name, account_type=payload.account_type)
    session.add(row)
    session.add(
        MembershipRecord(
            tenant_id=row.id,
            subject=principal.subject,
            email=payload.owner_email.lower(),
            role="admin",
        )
    )
    session.add(
        SubscriptionRecord(
            tenant_id=row.id,
            plan_code="individual" if payload.account_type == "INDIVIDUAL" else "small",
        )
    )
    session.add(
        AuditRecord(
            tenant_id=row.id,
            actor=principal.subject,
            action="organization.created",
            resource_id=row.id,
            payload={"account_type": row.account_type},
        )
    )
    await session.commit()
    return Organization(id=row.id, name=row.name, account_type=row.account_type, status=row.status)


async def list_workspaces(session: AsyncSession, principal: Principal) -> list[WorkspaceSummary]:
    rows = (
        await session.execute(
            select(OrganizationRecord, MembershipRecord.role)
            .join(MembershipRecord, MembershipRecord.tenant_id == OrganizationRecord.id)
            .where(
                MembershipRecord.subject == principal.subject, MembershipRecord.status == "ACTIVE"
            )
            .order_by(OrganizationRecord.name)
        )
    ).all()
    if not rows and principal.tenant_id == "demo":
        return [
            WorkspaceSummary(
                id="demo",
                name="Demo Workspace",
                account_type="ORGANIZATION",
                role="admin",
                status="ACTIVE",
            )
        ]
    return [
        WorkspaceSummary(
            id=org.id, name=org.name, account_type=org.account_type, role=role, status=org.status
        )
        for org, role in rows
    ]


async def list_members(session: AsyncSession, principal: Principal) -> list[Member]:
    require_role(principal, "admin", "viewer", "analyst", "reviewer", "executive")
    rows = list(
        await session.scalars(
            select(MembershipRecord).where(MembershipRecord.tenant_id == principal.tenant_id)
        )
    )
    return [
        Member(id=x.id, subject=x.subject, email=x.email, role=x.role, status=x.status)
        for x in rows
    ]


async def create_invitation(
    session: AsyncSession, principal: Principal, payload: InvitationCreate
) -> Invitation:
    require_role(principal, "admin")
    raw = secrets.token_urlsafe(32)
    row = InvitationRecord(
        tenant_id=principal.tenant_id,
        email=payload.email.lower(),
        role=payload.role,
        token_hash=sha256(raw.encode()).hexdigest(),
        invited_by=principal.subject,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    session.add(row)
    session.add(
        AuditRecord(
            tenant_id=principal.tenant_id,
            actor=principal.subject,
            action="member.invited",
            resource_id=row.id,
            payload={"email": row.email, "role": row.role},
        )
    )
    await session.commit()
    await session.refresh(row)
    return Invitation(
        id=row.id,
        email=row.email,
        role=row.role,
        status=row.status,
        expires_at=row.expires_at,
        acceptance_token=raw,
    )


async def accept_invitation(
    session: AsyncSession, principal: Principal, payload: InvitationAccept
) -> Member:
    digest = sha256(payload.token.encode()).hexdigest()
    row = await session.scalar(
        select(InvitationRecord).where(InvitationRecord.token_hash == digest).with_for_update()
    )
    if not row or row.status != "PENDING" or row.expires_at < datetime.now(UTC):
        raise HTTPException(400, "Invitation is invalid or expired")
    if row.tenant_id != principal.tenant_id or row.email != payload.email.lower():
        raise HTTPException(403, "Invitation does not match authenticated tenant or email")
    member = MembershipRecord(
        tenant_id=row.tenant_id, subject=principal.subject, email=row.email, role=row.role
    )
    row.status = "ACCEPTED"
    session.add(member)
    session.add(
        AuditRecord(
            tenant_id=row.tenant_id,
            actor=principal.subject,
            action="member.joined",
            resource_id=member.id,
            payload={"role": row.role},
        )
    )
    await session.commit()
    await session.refresh(member)
    return Member(
        id=member.id,
        subject=member.subject,
        email=member.email,
        role=member.role,
        status=member.status,
    )


async def entitlement_status(session: AsyncSession, principal: Principal) -> EntitlementStatus:
    subscription = await session.get(SubscriptionRecord, principal.tenant_id)
    plan = subscription.plan_code if subscription else "individual"
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["individual"])
    rows = (
        await session.execute(
            select(UsageLedgerRecord.metric, func.sum(UsageLedgerRecord.quantity))
            .where(UsageLedgerRecord.tenant_id == principal.tenant_id)
            .group_by(UsageLedgerRecord.metric)
        )
    ).all()
    usage = {metric: int(value) for metric, value in rows}
    return EntitlementStatus(
        plan_code=plan,
        subscription_status=subscription.status if subscription else "UNCONFIGURED",
        limits=limits,
        usage=usage,
        remaining={key: max(0, value - usage.get(key, 0)) for key, value in limits.items()},
    )


async def consume_entitlement(
    session: AsyncSession,
    principal: Principal,
    metric: str,
    quantity: int,
    key: str,
    resource_id: str | None = None,
) -> None:
    status = await entitlement_status(session, principal)
    if metric not in status.limits or quantity < 1:
        raise HTTPException(400, "Unknown or invalid entitlement metric")
    if status.remaining[metric] < quantity:
        raise HTTPException(402, f"{metric} quota exceeded")
    existing = await session.scalar(
        select(UsageLedgerRecord).where(UsageLedgerRecord.idempotency_key == key)
    )
    if not existing:
        session.add(
            UsageLedgerRecord(
                tenant_id=principal.tenant_id,
                metric=metric,
                quantity=quantity,
                idempotency_key=key,
                resource_id=resource_id,
            )
        )


def connector_capabilities() -> list[ProviderCapability]:
    return [
        ProviderCapability(
            provider="gmail",
            status="AVAILABLE",
            modes=["manual", "filtered_sync", "selected_message"],
            detail="OAuth read-only ingestion; selected-message add-in contract available.",
        ),
        ProviderCapability(
            provider="microsoft",
            status="CONFIGURATION_REQUIRED",
            modes=["manual", "selected_message", "consented_monitoring"],
            detail=(
                "Microsoft Graph adapter contract ready; Entra credentials and "
                "admin consent required."
            ),
        ),
    ]


async def historical_similarity(
    session: AsyncSession, principal: Principal, case_id: str
) -> list[SimilarityMatch]:
    source = await session.scalar(
        select(CaseRecord).where(
            CaseRecord.id == case_id,
            CaseRecord.tenant_id == principal.tenant_id,
            CaseRecord.deleted_at.is_(None),
        )
    )
    if not source:
        raise HTTPException(404, "Case not found")
    candidates = list(
        await session.scalars(
            select(CaseRecord).where(
                CaseRecord.tenant_id == principal.tenant_id,
                CaseRecord.id != case_id,
                CaseRecord.deleted_at.is_(None),
            )
        )
    )
    source_words = set(source.subject.lower().split())
    matches = []
    for row in candidates:
        words = set(row.subject.lower().split())
        union = source_words | words
        score = len(source_words & words) / len(union) if union else 0
        if row.case_type == source.case_type:
            score = min(1.0, score + 0.25)
        if score >= 0.25:
            matches.append(
                SimilarityMatch(
                    case_id=row.id,
                    subject=row.subject,
                    similarity=round(score, 3),
                    rationale=["same investigation type"]
                    if row.case_type == source.case_type
                    else ["subject token overlap"],
                )
            )
    return sorted(matches, key=lambda item: item.similarity, reverse=True)[:10]
