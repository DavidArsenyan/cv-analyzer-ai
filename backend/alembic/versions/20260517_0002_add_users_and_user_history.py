"""add users and user history

Revision ID: 20260517_0002
Revises: 20260515_0001
Create Date: 2026-05-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260517_0002"
down_revision: str | None = "20260515_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    with op.batch_alter_table("analysis_records") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_analysis_records_user_id"), ["user_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_analysis_records_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )
    op.execute("DELETE FROM analysis_records WHERE user_id IS NULL")
    with op.batch_alter_table("analysis_records") as batch_op:
        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("analysis_records") as batch_op:
        batch_op.drop_constraint("fk_analysis_records_user_id_users", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_analysis_records_user_id"))
        batch_op.drop_column("user_id")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
