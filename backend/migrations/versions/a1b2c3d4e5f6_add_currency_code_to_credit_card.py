"""add currency_code to credit_card

Revision ID: a1b2c3d4e5f6
Revises: ccc65562e43f
Create Date: 2026-07-25 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "ccc65562e43f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "credit_card",
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="DOP"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("credit_card", "currency_code")
