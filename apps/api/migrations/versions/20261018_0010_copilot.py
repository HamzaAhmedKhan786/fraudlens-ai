"""persistent investigation copilot

Revision ID: 20261018_0010
Revises: 20261018_0009
"""

import sqlalchemy as sa
from alembic import op

revision = "20261018_0010"
down_revision = "20261018_0009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column(
            "case_id", sa.String(100), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_conversations_tenant_id", "chat_conversations", ["tenant_id"])
    op.create_index("ix_chat_conversations_case_id", "chat_conversations", ["case_id"])
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(36),
            sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("created_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name in ("conversation_id", "tenant_id", "created_at"):
        op.create_index(f"ix_chat_messages_{name}", "chat_messages", [name])
    op.create_table(
        "chat_feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("case_id", sa.String(100), nullable=False),
        sa.Column(
            "message_id",
            sa.String(36),
            sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(160), nullable=False),
        sa.Column("rating", sa.String(32), nullable=False),
        sa.Column("explanation", sa.Text()),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("message_id", "user_id", name="uq_chat_feedback_user"),
    )
    for name in ("tenant_id", "case_id", "message_id"):
        op.create_index(f"ix_chat_feedback_{name}", "chat_feedback", [name])


def downgrade():
    op.drop_table("chat_feedback")
    op.drop_table("chat_messages")
    op.drop_table("chat_conversations")
