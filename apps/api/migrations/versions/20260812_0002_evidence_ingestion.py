"""Add secure evidence upload and processing state."""

import sqlalchemy as sa
from alembic import op

revision = "20260812_0002"
down_revision = "20260810_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "case_id", sa.String(100), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("declared_content_type", sa.String(120)),
        sa.Column("detected_content_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_bucket", sa.String(100), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False, unique=True),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("scan_status", sa.String(40), nullable=False),
        sa.Column("processing_attempts", sa.Integer(), nullable=False),
        sa.Column("extracted", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column("object_available", sa.Boolean(), nullable=False),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_uploads_case_id", "uploads", ["case_id"])
    op.create_index("ix_uploads_tenant_id", "uploads", ["tenant_id"])
    op.create_index("ix_uploads_sha256", "uploads", ["sha256"])
    op.create_index("ix_uploads_status", "uploads", ["status"])
    op.create_index("ix_uploads_created_at", "uploads", ["created_at"])
    op.create_index("ix_uploads_retention_expires_at", "uploads", ["retention_expires_at"])
    op.create_index("ix_uploads_metadata_expires_at", "uploads", ["metadata_expires_at"])
    op.create_index(
        "uq_uploads_tenant_sha256",
        "uploads",
        ["tenant_id", "sha256"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("uploads")
