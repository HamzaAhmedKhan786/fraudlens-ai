"""Add tenant-scoped human review queue."""

import sqlalchemy as sa
from alembic import op

revision = "20261018_0007"
down_revision = "20261018_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "case_id", sa.String(100), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("requester", sa.String(160), nullable=False),
        sa.Column("request_type", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("reviewer", sa.String(160), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "tenant_id", "request_type", "status", "created_at"):
        op.create_index(f"ix_review_requests_{column}", "review_requests", [column])


def downgrade() -> None:
    op.drop_table("review_requests")
