"""add currency_code to budget

Revision ID: 9c6d7e8f0a1b
Revises: 8d5e6f7a9b0c
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "9c6d7e8f0a1b"
down_revision: Union[str, None] = "8d5e6f7a9b0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "budget",
        sa.Column(
            "currency_code",
            sa.String(length=3),
            server_default="DOP",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("budget", "currency_code")
