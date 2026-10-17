"""Store public intelligence with provenance."""

import sqlalchemy as sa
from alembic import op

revision = "20261017_0004"
down_revision = "20261003_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "public_intelligence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("indicator_type", sa.String(40), nullable=False),
        sa.Column("indicator", sa.String(500), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("source_uri", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("facts", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("tenant_id", "indicator_type", "indicator", "fetched_at"):
        op.create_index(f"ix_public_intelligence_{column}", "public_intelligence", [column])


def downgrade() -> None:
    op.drop_table("public_intelligence")
