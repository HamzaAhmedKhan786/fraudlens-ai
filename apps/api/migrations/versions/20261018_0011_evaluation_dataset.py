"""reviewed copilot evaluation dataset
Revision ID: 20261018_0011
Revises: 20261018_0010
"""

import sqlalchemy as sa
from alembic import op

revision = "20261018_0011"
down_revision = "20261018_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "evaluation_examples",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("case_id", sa.String(100), nullable=False),
        sa.Column("message_id", sa.String(36), nullable=False),
        sa.Column("feedback_id", sa.String(36), nullable=False, unique=True),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("expected_assessment", sa.Text(), nullable=False),
        sa.Column("approved_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name in ("tenant_id", "case_id", "message_id"):
        op.create_index(f"ix_evaluation_examples_{name}", "evaluation_examples", [name])


def downgrade():
    op.drop_table("evaluation_examples")
