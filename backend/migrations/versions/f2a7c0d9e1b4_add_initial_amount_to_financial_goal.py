"""add_initial_amount_to_financial_goal

Revision ID: f2a7c0d9e1b4
Revises: 739674bb3188
Create Date: 2026-07-31 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f2a7c0d9e1b4"
down_revision: Union[str, Sequence[str], None] = "739674bb3188"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "financial_goal",
        sa.Column(
            "initial_amount", sa.Numeric(precision=19, scale=4), server_default="0", nullable=False
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("financial_goal", "initial_amount")
