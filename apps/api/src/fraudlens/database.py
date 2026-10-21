from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from fraudlens.config import get_settings


class Base(DeclarativeBase):
    pass


class CaseRecord(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    subject: Mapped[str] = mapped_column(String(240))
    case_type: Mapped[str] = mapped_column(String(80))
    analysis_modules: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_sources: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40), default="OPEN", index=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[str] = mapped_column(String(20), default="LOW")
    assignee: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    disposition: Mapped[str | None] = mapped_column(String(40), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    deleted_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    delete_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    evidence: Mapped[list["EvidenceRecord"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    investigations: Mapped[list["InvestigationRecord"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    uploads: Mapped[list["UploadRecord"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    comments: Mapped[list["CaseCommentRecord"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )


class CaseCommentRecord(Base):
    __tablename__ = "case_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    author: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    case: Mapped[CaseRecord] = relationship(back_populates="comments")


class WorkspaceSettingsRecord(Base):
    __tablename__ = "workspace_settings"

    tenant_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    mandatory_human_review: Mapped[bool] = mapped_column(default=True)
    llm_narrative_enabled: Mapped[bool] = mapped_column(default=False)
    critical_risk_threshold: Mapped[int] = mapped_column(Integer, default=80)
    evidence_retention_days: Mapped[int] = mapped_column(Integer, default=180)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class PolicyRecord(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(40))
    enabled: Mapped[bool] = mapped_column(default=True)
    threshold: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    source: Mapped[str] = mapped_column(String(500))
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    deleted_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    delete_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    case: Mapped[CaseRecord] = relationship(back_populates="evidence")


class InvestigationRecord(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="COMPLETED")
    risk_score: Mapped[int] = mapped_column(Integer)
    severity: Mapped[str] = mapped_column(String(20))
    report: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    case: Mapped[CaseRecord] = relationship(back_populates="investigations")


class AuditRecord(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(160))
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_id: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )


class ReviewRequestRecord(Base):
    __tablename__ = "review_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    requester: Mapped[str] = mapped_column(String(160))
    request_type: Mapped[str] = mapped_column(String(40), index=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="PENDING", index=True)
    reviewer: Mapped[str | None] = mapped_column(String(160), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class UploadRecord(Base):
    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    declared_content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detected_content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_bucket: Mapped[str] = mapped_column(String(100))
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    status: Mapped[str] = mapped_column(String(40), default="RECEIVED", index=True)
    scan_status: Mapped[str] = mapped_column(String(40), default="PENDING")
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0)
    extracted: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_available: Mapped[bool] = mapped_column(default=True)
    retention_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    case: Mapped[CaseRecord] = relationship(back_populates="uploads")


class PublicIntelligenceRecord(Base):
    __tablename__ = "public_intelligence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    indicator_type: Mapped[str] = mapped_column(String(40), index=True)
    indicator: Mapped[str] = mapped_column(String(500), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    source_uri: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(40), default="OBSERVED")
    facts: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )


class GmailOAuthStateRecord(Base):
    __tablename__ = "gmail_oauth_states"

    state_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(160))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GmailConnectionRecord(Base):
    __tablename__ = "gmail_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email_address: Mapped[str] = mapped_column(String(320))
    encrypted_refresh_token: Mapped[str] = mapped_column(Text)
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40), default="CONNECTED")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OrganizationRecord(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(240))
    account_type: Mapped[str] = mapped_column(String(24), default="ORGANIZATION")
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class MembershipRecord(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "subject", name="uq_membership_tenant_subject"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    subject: Mapped[str] = mapped_column(String(160), index=True)
    email: Mapped[str] = mapped_column(String(320))
    role: Mapped[str] = mapped_column(String(24), default="viewer")
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class InvitationRecord(Base):
    __tablename__ = "invitations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    role: Mapped[str] = mapped_column(String(24))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    invited_by: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24), default="PENDING")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class SubscriptionRecord(Base):
    __tablename__ = "subscriptions"
    tenant_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    plan_code: Mapped[str] = mapped_column(String(40), default="individual")
    status: Mapped[str] = mapped_column(String(24), default="TRIAL")
    provider_customer_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class UsageLedgerRecord(Base):
    __tablename__ = "usage_ledger"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    metric: Mapped[str] = mapped_column(String(40), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )


class EmailConnectorRecord(Base):
    __tablename__ = "email_connectors"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", name="uq_email_connector_provider"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    account_address: Mapped[str] = mapped_column(String(320))
    encrypted_refresh_token: Mapped[str] = mapped_column(Text)
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    consent_mode: Mapped[str] = mapped_column(String(24), default="MANUAL")
    status: Mapped[str] = mapped_column(String(24), default="CONNECTED")
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class OutboxEventRecord(Base):
    __tablename__ = "outbox_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    topic: Mapped[str] = mapped_column(String(160), index=True)
    aggregate_id: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default="PENDING", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChatConversationRecord(Base):
    __tablename__ = "chat_conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ChatMessageRecord(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("chat_conversations.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[str]] = mapped_column(JSON, default=list)
    model: Mapped[str] = mapped_column(String(120))
    created_by: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )


class ChatFeedbackRecord(Base):
    __tablename__ = "chat_feedback"
    __table_args__ = (UniqueConstraint("message_id", "user_id", name="uq_chat_feedback_user"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    case_id: Mapped[str] = mapped_column(String(100), index=True)
    message_id: Mapped[str] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(160))
    rating: Mapped[str] = mapped_column(String(32))
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(120))
    reviewed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class EvaluationExampleRecord(Base):
    __tablename__ = "evaluation_examples"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    case_id: Mapped[str] = mapped_column(String(100), index=True)
    message_id: Mapped[str] = mapped_column(String(36), index=True)
    feedback_id: Mapped[str] = mapped_column(String(36), unique=True)
    input_snapshot: Mapped[dict[str, object]] = mapped_column(JSON)
    expected_assessment: Mapped[str] = mapped_column(Text)
    approved_by: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def create_schema() -> None:
    # Local bootstrap only. Production deploys should run Alembic before starting the API.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def seed_demo_data() -> None:
    async with session_factory() as session:
        existing = await session.scalar(select(CaseRecord.id).limit(1))
        if existing:
            return
        demo = [
            CaseRecord(
                id="FR-29482",
                tenant_id="demo",
                subject="Northstar Components",
                case_type="Invoice + email",
                status="UNDER_REVIEW",
                risk_score=92,
                severity="CRITICAL",
            ),
            CaseRecord(
                id="FR-29479",
                tenant_id="demo",
                subject="Executive payment request",
                case_type="BEC",
                status="OPEN",
                risk_score=78,
                severity="HIGH",
            ),
            CaseRecord(
                id="FR-29471",
                tenant_id="demo",
                subject="Identity verification",
                case_type="ID + video",
                status="OPEN",
                risk_score=64,
                severity="HIGH",
            ),
            CaseRecord(
                id="FR-29464",
                tenant_id="demo",
                subject="Refund evidence",
                case_type="Image",
                status="OPEN",
                risk_score=37,
                severity="MEDIUM",
            ),
        ]
        session.add_all(demo)
        await session.commit()
