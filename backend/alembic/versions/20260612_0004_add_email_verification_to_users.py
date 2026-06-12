"""add email verification to users

Revision ID: 20260612_0004
Revises: 20260610_0003
Create Date: 2026-06-12
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260612_0004"
down_revision: Union[str, None] = "20260610_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("is_email_verified", sa.Boolean(), server_default=sa.true(), nullable=False))
        batch_op.add_column(sa.Column("email_verification_code_hash", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("email_verification_expires_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column("email_verification_attempts", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.add_column(sa.Column("email_verification_sent_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("email_verification_sent_at")
        batch_op.drop_column("email_verification_attempts")
        batch_op.drop_column("email_verification_expires_at")
        batch_op.drop_column("email_verification_code_hash")
        batch_op.drop_column("is_email_verified")
