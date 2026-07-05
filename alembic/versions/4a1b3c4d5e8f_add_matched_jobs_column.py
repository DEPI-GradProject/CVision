"""add matched_jobs column to analysis_history

Revision ID: 4a1b3c4d5e8f
Revises: 3a1b3c4d5e7f
Create Date: 2026-07-05 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4a1b3c4d5e8f"
down_revision: str | None = "3a1b3c4d5e7f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("analysis_history", sa.Column("matched_jobs", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analysis_history", "matched_jobs")
