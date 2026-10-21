"""add recoverable case and evidence deletion

Revision ID: 20261018_0008
Revises: 20261018_0007
"""

import sqlalchemy as sa
from alembic import op

revision = "20261018_0008"
down_revision = "20261018_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("cases", "evidence"):
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("deleted_by", sa.String(length=160), nullable=True))
        op.add_column(table, sa.Column("delete_reason", sa.Text(), nullable=True))
        op.create_index(f"ix_{table}_deleted_at", table, ["deleted_at"])


def downgrade() -> None:
    for table in ("evidence", "cases"):
        op.drop_index(f"ix_{table}_deleted_at", table_name=table)
        op.drop_column(table, "delete_reason")
        op.drop_column(table, "deleted_by")
        op.drop_column(table, "deleted_at")
