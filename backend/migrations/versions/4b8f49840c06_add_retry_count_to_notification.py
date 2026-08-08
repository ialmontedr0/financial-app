"""add retry_count to notification

Revision ID: 4b8f49840c06
Revises: 7c8be4bb3e6e
Create Date: 2026-08-06 11:35:16.169388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b8f49840c06'
down_revision: Union[str, Sequence[str], None] = '7c8be4bb3e6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "notification",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("notification", "retry_count")
