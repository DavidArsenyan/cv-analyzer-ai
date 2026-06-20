"""add password reset to users

Revision ID: 20260621_0005
Revises: 20260612_0004
Create Date: 2026-06-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260621_0005"
down_revision: str | None = "20260612_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_reset_code_hash", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("password_reset_expires_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("password_reset_attempts", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("password_reset_sent_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_reset_sent_at")
        batch_op.drop_column("password_reset_attempts")
        batch_op.drop_column("password_reset_expires_at")
        batch_op.drop_column("password_reset_code_hash")
