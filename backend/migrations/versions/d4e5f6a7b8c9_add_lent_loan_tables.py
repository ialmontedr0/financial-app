"""add_lent_loan_tables

Revision ID: d4e5f6a7b8c9
Revises: 9a1b2c3d4e5f
Create Date: 2026-08-07 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as sa_pg

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "9a1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    frequency_enum = sa_pg.ENUM(
        "monthly", "bi_weekly", "weekly", name="lent_loan_frequency_enum",
        create_type=False,
    )
    status_enum = sa_pg.ENUM(
        "active", "paid_off", "defaulted", "cancelled", name="lent_loan_status_enum",
        create_type=False,
    )
    op.execute("CREATE TYPE lent_loan_frequency_enum AS ENUM ('monthly', 'bi_weekly', 'weekly')")
    op.execute(
        "CREATE TYPE lent_loan_status_enum AS ENUM ('active', 'paid_off', 'defaulted', 'cancelled')"
    )

    op.create_table(
        "lent_loan",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("account_id", sa.UUID(), sa.ForeignKey("financial_account.id", ondelete="SET NULL"), nullable=True),
        sa.Column("borrower_name", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("principal_amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("annual_interest_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("term_months", sa.Integer(), nullable=False),
        sa.Column("payment_frequency", frequency_enum, nullable=False, server_default="monthly"),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="DOP"),
        sa.Column("monthly_payment", sa.Numeric(19, 4), nullable=False),
        sa.Column("current_balance", sa.Numeric(19, 4), nullable=False),
        sa.Column("total_received", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("total_interest_expected", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("total_interest_received", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("first_payment_date", sa.Date(), nullable=True),
        sa.Column("next_payment_date", sa.Date(), nullable=True),
        sa.Column("final_payment_date", sa.Date(), nullable=True),
        sa.Column("paid_off_date", sa.Date(), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default="active"),
        sa.Column("is_collateralized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_lent_loan_user_status", "lent_loan", ["user_id", "status"])
    op.create_index("ix_lent_loan_user_term", "lent_loan", ["user_id", "term_months"])

    op.create_table(
        "lent_loan_payment",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("lent_loan_id", sa.UUID(), sa.ForeignKey("lent_loan.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("principal_portion", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("interest_portion", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=False, server_default="bank_transfer"),
        sa.Column("reference_number", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_lent_loan_payment_loan", "lent_loan_payment", ["lent_loan_id"])


def downgrade() -> None:
    op.drop_table("lent_loan_payment")
    op.drop_table("lent_loan")
    sa_pg.ENUM(name="lent_loan_frequency_enum").drop(op.get_bind(), checkfirst=True)
    sa_pg.ENUM(name="lent_loan_status_enum").drop(op.get_bind(), checkfirst=True)
