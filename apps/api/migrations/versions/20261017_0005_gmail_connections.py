"""Add tenant Gmail OAuth connections."""

import sqlalchemy as sa
from alembic import op

revision = "20261017_0005"
down_revision = "20261017_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gmail_oauth_states",
        sa.Column("state_hash", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(160), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gmail_oauth_states_tenant_id", "gmail_oauth_states", ["tenant_id"])
    op.create_index("ix_gmail_oauth_states_expires_at", "gmail_oauth_states", ["expires_at"])
    op.create_table(
        "gmail_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, unique=True),
        sa.Column("email_address", sa.String(320), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gmail_connections_tenant_id", "gmail_connections", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("gmail_connections")
    op.drop_table("gmail_oauth_states")
