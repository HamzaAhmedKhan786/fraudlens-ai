"""Add persisted case workflow, policies, and workspace settings."""

import sqlalchemy as sa
from alembic import op

revision = "20261003_0003"
down_revision = "20260812_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("assignee", sa.String(160), nullable=True))
    op.add_column("cases", sa.Column("disposition", sa.String(40), nullable=True))
    op.create_index("ix_cases_assignee", "cases", ["assignee"])
    op.create_table(
        "case_comments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(100), sa.ForeignKey("cases.id", ondelete="CASCADE")),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("author", sa.String(160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_comments_case_id", "case_comments", ["case_id"])
    op.create_index("ix_case_comments_tenant_id", "case_comments", ["tenant_id"])
    op.create_index("ix_case_comments_created_at", "case_comments", ["created_at"])
    op.create_table(
        "workspace_settings",
        sa.Column("tenant_id", sa.String(100), primary_key=True),
        sa.Column("mandatory_human_review", sa.Boolean(), nullable=False),
        sa.Column("llm_narrative_enabled", sa.Boolean(), nullable=False),
        sa.Column("critical_risk_threshold", sa.Integer(), nullable=False),
        sa.Column("evidence_retention_days", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "policies",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("tenant_id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_policies_tenant_id", "policies", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("policies")
    op.drop_table("workspace_settings")
    op.drop_table("case_comments")
    op.drop_index("ix_cases_assignee", table_name="cases")
    op.drop_column("cases", "disposition")
    op.drop_column("cases", "assignee")
