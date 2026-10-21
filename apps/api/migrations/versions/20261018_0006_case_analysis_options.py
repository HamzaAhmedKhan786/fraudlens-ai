"""Persist investigation analysis modules and evidence sources."""

import sqlalchemy as sa
from alembic import op

revision = "20261018_0006"
down_revision = "20261017_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cases", sa.Column("analysis_modules", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "cases", sa.Column("evidence_sources", sa.JSON(), nullable=False, server_default="[]")
    )


def downgrade() -> None:
    op.drop_column("cases", "evidence_sources")
    op.drop_column("cases", "analysis_modules")
