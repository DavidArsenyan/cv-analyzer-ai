"""add target role to analysis records

Revision ID: 20260610_0003
Revises: 20260517_0002
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260610_0003"
down_revision: str | None = "20260517_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("analysis_records") as batch_op:
        batch_op.add_column(sa.Column("target_role", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("analysis_records") as batch_op:
        batch_op.drop_column("target_role")
