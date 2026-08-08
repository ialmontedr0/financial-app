"""add last_payment_date to loan

Revision ID: 79741a05c822
Revises: 4b8f49840c06
Create Date: 2026-08-06 11:52:07.440112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79741a05c822'
down_revision: Union[str, Sequence[str], None] = '4b8f49840c06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("loan", sa.Column("last_payment_date", sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("loan", "last_payment_date")
