"""Create widgets table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260516_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "widgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_widgets_name"),
    )
    op.create_index(op.f("ix_widgets_name"), "widgets", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_widgets_name"), table_name="widgets")
    op.drop_table("widgets")
