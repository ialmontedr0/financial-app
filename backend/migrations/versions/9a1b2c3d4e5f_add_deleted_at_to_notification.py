"""add deleted_at to notification (soft delete)

Revision ID: 9a1b2c3d4e5f
Revises: 79741a05c822
Create Date: 2026-08-06 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: str | Sequence[str] | None = '79741a05c822'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "notification",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notification_deleted_at", "notification", ["deleted_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_notification_deleted_at", table_name="notification")
    op.drop_column("notification", "deleted_at")
