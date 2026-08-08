"""add_single_payment_frequency_to_lent_loans

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-08 12:00:00.000000

Adds the ``single_payment`` frequency to ``lent_loan_frequency_enum`` and a
``single_payment_date`` column so the user can set the month/year the debtor
will repay the loan in one lump sum.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE lent_loan_frequency_enum ADD VALUE IF NOT EXISTS 'single_payment'"
    )
    op.add_column(
        "lent_loan",
        sa.Column("single_payment_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lent_loan", "single_payment_date")
    op.execute("ALTER TABLE lent_loan ALTER COLUMN payment_frequency DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE lent_loan ALTER COLUMN payment_frequency TYPE varchar
        """
    )
    op.execute("DROP TYPE IF EXISTS lent_loan_frequency_enum")
    op.execute(
        "CREATE TYPE lent_loan_frequency_enum AS ENUM "
        "('monthly', 'bi_weekly', 'weekly')"
    )
    op.execute(
        """
        ALTER TABLE lent_loan
        ALTER COLUMN payment_frequency
        TYPE lent_loan_frequency_enum
        USING payment_frequency::lent_loan_frequency_enum
        """
    )
    op.execute(
        """
        ALTER TABLE lent_loan
        ALTER COLUMN payment_frequency
        SET DEFAULT 'monthly'::lent_loan_frequency_enum
        """
    )
