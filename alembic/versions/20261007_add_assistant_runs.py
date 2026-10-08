"""Persist auditable assistant approvals.

Revision ID: 20261007_assistant_runs
Revises: d309e807b2ec
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261007_assistant_runs"
down_revision = "d309e807b2ec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assistant_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("requested_by", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("preview", postgresql.JSONB(), nullable=False),
        sa.Column("answer", sa.String(), nullable=True),
        sa.Column("approved_by", sa.String(30), nullable=True),
        sa.Column("decision", sa.Boolean(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("assistant_runs")
