"""create analysis records

Revision ID: 20260515_0001
Revises:
Create Date: 2026-05-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260515_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("analysis_mode", sa.String(length=32), nullable=False),
        sa.Column("ats_score", sa.Integer(), nullable=False),
        sa.Column("job_match_score", sa.Integer(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_records_id"), "analysis_records", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_records_id"), table_name="analysis_records")
    op.drop_table("analysis_records")
