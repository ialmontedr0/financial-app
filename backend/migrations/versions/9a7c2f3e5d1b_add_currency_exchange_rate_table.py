"""add currency_exchange_rate table

Revision ID: 9a7c2f3e5d1b
Revises: 8f2e1d4c9b7a
Create Date: 2026-08-01 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "9a7c2f3e5d1b"
down_revision: str | None = "8f2e1d4c9b7a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "currency_exchange_rate",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_currency", sa.String(length=3), nullable=False),
        sa.Column("target_currency", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_currency",
            "target_currency",
            "rate_date",
            name="uq_currency_exchange_rate_pair_date",
        ),
    )
    op.create_index(
        "ix_currency_exchange_rate_source_currency",
        "currency_exchange_rate",
        ["source_currency"],
    )
    op.create_index(
        "ix_currency_exchange_rate_target_currency",
        "currency_exchange_rate",
        ["target_currency"],
    )
    op.create_index(
        "ix_currency_exchange_rate_rate_date",
        "currency_exchange_rate",
        ["rate_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_currency_exchange_rate_rate_date",
        table_name="currency_exchange_rate",
    )
    op.drop_index(
        "ix_currency_exchange_rate_target_currency",
        table_name="currency_exchange_rate",
    )
    op.drop_index(
        "ix_currency_exchange_rate_source_currency",
        table_name="currency_exchange_rate",
    )
    op.drop_table("currency_exchange_rate")
