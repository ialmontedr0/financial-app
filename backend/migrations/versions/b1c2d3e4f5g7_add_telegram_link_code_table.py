"""add_telegram_link_code_table

Revision ID: b1c2d3e4f5g7
Revises: a1b2c3d4e5f7
Create Date: 2026-07-29 13:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b1c2d3e4f5g7"
down_revision: Union[str, Sequence[str], None] = "9e1455a1cbd7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_link_code",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(6), nullable=False, index=True),
        sa.Column("is_used", sa.Boolean(), default=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("telegram_link_code")
