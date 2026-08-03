"""add domain_event table

Revision ID: 8f2e1d4c9b7a
Revises: 76433162681b
Create Date: 2026-08-01 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "8f2e1d4c9b7a"
down_revision: str | None = "76433162681b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "domain_event",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("aggregate_id", UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_type", sa.String(length=50), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("data", JSONB(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="published", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domain_event_event_type", "domain_event", ["event_type"])
    op.create_index("ix_domain_event_aggregate_id", "domain_event", ["aggregate_id"])
    op.create_index("ix_domain_event_user_id", "domain_event", ["user_id"])
    op.create_index("ix_domain_event_type_status", "domain_event", ["event_type", "status"])


def downgrade() -> None:
    op.drop_index("ix_domain_event_type_status", table_name="domain_event")
    op.drop_index("ix_domain_event_user_id", table_name="domain_event")
    op.drop_index("ix_domain_event_aggregate_id", table_name="domain_event")
    op.drop_index("ix_domain_event_event_type", table_name="domain_event")
    op.drop_table("domain_event")
