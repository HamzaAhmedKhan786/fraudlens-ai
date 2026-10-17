from datetime import UTC, datetime

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal
from fraudlens.database import AuditRecord, PublicIntelligenceRecord
from fraudlens.schemas import PublicIntelligence


def _view(record: PublicIntelligenceRecord) -> PublicIntelligence:
    return PublicIntelligence(
        id=record.id,
        indicator_type=record.indicator_type,
        indicator=record.indicator,
        provider=record.provider,
        source_uri=record.source_uri,
        status=record.status,
        facts=record.facts,
        fetched_at=record.fetched_at,
    )


async def lookup_domain(
    session: AsyncSession, principal: Principal, raw_domain: str
) -> PublicIntelligence:
    domain = raw_domain.strip().strip(".").lower()
    labels = domain.split(".")
    invalid_label = any(
        not label or label.startswith("-") or label.endswith("-") for label in labels
    )
    if len(labels) < 2 or invalid_label:
        raise HTTPException(status_code=422, detail="Enter a valid registrable domain")
    try:
        ascii_domain = domain.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid internationalized domain") from exc

    source_uri = f"https://rdap.org/domain/{ascii_domain}"
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(
                source_uri,
                headers={"Accept": "application/rdap+json", "User-Agent": "FraudLens/0.1"},
            )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502, detail="RDAP provider did not return usable data"
        ) from exc

    events = {
        item.get("eventAction"): item.get("eventDate")
        for item in payload.get("events", [])
        if item.get("eventAction") and item.get("eventDate")
    }
    nameservers = sorted(
        {
            item.get("ldhName", "").lower()
            for item in payload.get("nameservers", [])
            if item.get("ldhName")
        }
    )
    facts: dict[str, object] = {
        "handle": payload.get("handle"),
        "registration_date": events.get("registration"),
        "expiration_date": events.get("expiration"),
        "last_changed": events.get("last changed"),
        "rdap_status": payload.get("status", []),
        "nameservers": nameservers,
        "port43": payload.get("port43"),
        "notice": "Registration facts are context, not proof of fraud.",
    }
    record = PublicIntelligenceRecord(
        tenant_id=principal.tenant_id,
        indicator_type="domain",
        indicator=ascii_domain,
        provider="ICANN RDAP bootstrap",
        source_uri=str(response.url),
        status="OBSERVED",
        facts=facts,
        fetched_at=datetime.now(UTC),
    )
    session.add(record)
    session.add(
        AuditRecord(
            tenant_id=principal.tenant_id,
            actor=principal.actor,
            action="public_intelligence.domain_fetched",
            resource_id=ascii_domain,
            payload={"provider": record.provider, "source_uri": record.source_uri},
        )
    )
    await session.commit()
    await session.refresh(record)
    return _view(record)


async def list_public_intelligence(
    session: AsyncSession, principal: Principal
) -> list[PublicIntelligence]:
    records = (
        await session.scalars(
            select(PublicIntelligenceRecord)
            .where(PublicIntelligenceRecord.tenant_id == principal.tenant_id)
            .order_by(PublicIntelligenceRecord.fetched_at.desc())
            .limit(100)
        )
    ).all()
    return [_view(record) for record in records]
