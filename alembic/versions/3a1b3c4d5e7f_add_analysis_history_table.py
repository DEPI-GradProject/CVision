"""add analysis_history table

Revision ID: 3a1b3c4d5e7f
Revises: 2a1b3c4d5e6f
Create Date: 2026-07-02 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3a1b3c4d5e7f"
down_revision: str | None = "2a1b3c4d5e6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("ats_score", sa.Integer(), nullable=True),
        sa.Column("skills_extracted", sa.Text(), nullable=True),
        sa.Column("job_matches", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_history_user_id"), "analysis_history", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_history_user_id"), table_name="analysis_history")
    op.drop_table("analysis_history")
