"""initial schema

Revision ID: 26e48f4660ab
Revises:
Create Date: 2026-05-12 00:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "26e48f4660ab"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs_raw",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("job_link", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("published_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_link"),
    )

    op.create_table(
        "training_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("Title", sa.String(length=255), nullable=False),
        sa.Column("Link", sa.String(), nullable=True),
        sa.Column("Skills", sa.Text(), nullable=True),
        sa.Column("Price", sa.String(length=50), nullable=True),
        sa.Column("Description", sa.Text(), nullable=True),
        sa.Column("platform_source", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("training_jobs")
    op.drop_table("jobs_raw")
