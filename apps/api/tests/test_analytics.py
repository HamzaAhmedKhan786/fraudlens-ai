from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from fraudlens.analytics import overview, search_cases
from fraudlens.auth import Principal
from fraudlens.database import Base, CaseRecord, EvidenceRecord, InvestigationRecord
from fraudlens.services import investigate_case
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_analytics_and_search_exclude_other_tenants_and_deleted_cases(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'analytics.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    try:
        async with sessions() as session:
            session.add_all(
                [
                    CaseRecord(
                        id="A-001",
                        tenant_id="alpha",
                        subject="Invoice 100% verified",
                        case_type="Invoice",
                        status="OPEN",
                        risk_score=85,
                        severity="CRITICAL",
                    ),
                    CaseRecord(
                        id="A-002",
                        tenant_id="alpha",
                        subject="Normal email",
                        case_type="Email",
                        status="RESOLVED",
                        risk_score=5,
                        severity="LOW",
                    ),
                    CaseRecord(
                        id="A-OLD",
                        tenant_id="alpha",
                        subject="Deleted",
                        case_type="Invoice",
                        risk_score=100,
                        severity="CRITICAL",
                        deleted_at=now,
                    ),
                    CaseRecord(
                        id="B-001",
                        tenant_id="beta",
                        subject="Other tenant secret",
                        case_type="Invoice",
                        risk_score=100,
                        severity="CRITICAL",
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    InvestigationRecord(
                        id="run-alpha",
                        case_id="A-001",
                        risk_score=85,
                        severity="CRITICAL",
                        report={"findings": []},
                        created_at=now,
                    ),
                    InvestigationRecord(
                        id="run-deleted",
                        case_id="A-OLD",
                        risk_score=100,
                        severity="CRITICAL",
                        report={"secret": True},
                        created_at=now,
                    ),
                    InvestigationRecord(
                        id="run-beta",
                        case_id="B-001",
                        risk_score=100,
                        severity="CRITICAL",
                        report={"secret": True},
                        created_at=now,
                    ),
                    EvidenceRecord(
                        id="ev-1", case_id="A-001", kind="invoice", source="invoice.pdf"
                    ),
                    EvidenceRecord(
                        id="ev-deleted",
                        case_id="A-001",
                        kind="invoice",
                        source="deleted.pdf",
                        deleted_at=now,
                    ),
                ]
            )
            await session.commit()
            principal = Principal(subject="analyst", tenant_id="alpha", roles={"analyst"})
            result = await overview(session, principal, 7)
            assert result["summary"]["total_cases"] == 2
            assert result["summary"]["total_investigations"] == 1
            assert result["summary"]["open_cases"] == 1
            assert result["summary"]["average_risk"] == 45
            assert result["latest"]["id"] == "A-001"
            assert len(result["trend"]) == 7
            assert sum(day["completed"] for day in result["trend"]) == 1
            assert result["geography"]["available"] is False
            page = await search_cases(session, principal, query="100%", page_size=1)
            assert page["total"] == 1
            assert page["items"][0]["id"] == "A-001"
            assert page["items"][0]["evidence_count"] == 1
            empty = await search_cases(session, principal, query="secret")
            assert empty["total"] == 0
            second = await search_cases(session, principal, sort="risk", page=2, page_size=1)
            assert second["items"][0]["id"] == "A-002"
            empty_principal = Principal(subject="viewer", tenant_id="empty", roles={"viewer"})
            empty = await overview(session, empty_principal, 30)
            assert empty["summary"]["total_cases"] == 0
            assert empty["latest"] is None
            assert all(
                day["date"] >= (now - timedelta(days=29)).date().isoformat()
                for day in empty["trend"]
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_viewer_cannot_rerun_an_investigation():
    viewer = Principal(subject="viewer", tenant_id="alpha", roles={"viewer"})
    with pytest.raises(HTTPException) as denied:
        await investigate_case(None, viewer, "A-001", None)
    assert denied.value.status_code == 403
