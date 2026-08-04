"""add idempotency_keys table and version columns

Revision ID: 7c4d5e6f8a9b
Revises: 9b3f2a7c1d5e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "7c4d5e6f8a9b"
down_revision: Union[str, None] = "9b3f2a7c1d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_unique_constraint("uq_idempotency_keys_key", "idempotency_keys", ["key"])

    for table in ("financial_account", "financial_goal", "budget"):
        op.add_column(table, sa.Column("version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    for table in ("financial_account", "financial_goal", "budget"):
        op.drop_column(table, "version")
    op.drop_table("idempotency_keys")
