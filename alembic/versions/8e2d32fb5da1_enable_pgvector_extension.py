"""enable pgvector extension

Revision ID: 8e2d32fb5da1
Revises: 4a8850d12a0d
Create Date: 2026-09-04 21:31:59.413701

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e2d32fb5da1"
down_revision: str | Sequence[str] | None = "4a8850d12a0d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
