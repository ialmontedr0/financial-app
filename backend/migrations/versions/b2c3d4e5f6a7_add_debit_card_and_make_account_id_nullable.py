"""add debit_card table, make credit_card.account_id nullable, make transaction.account_id nullable, add multi-currency to credit_card

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-26 09:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create debit_card table
    op.create_table(
        "debit_card",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "account_id",
            UUID(as_uuid=True),
            sa.ForeignKey("financial_account.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("last_four_digits", sa.String(4), nullable=True),
        sa.Column("card_network", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Make credit_card.account_id nullable
    op.alter_column(
        "credit_card",
        "account_id",
        existing_type=UUID(as_uuid=True),
        nullable=True,
        existing_server_default=None,
    )

    # Add multi-currency columns to credit_card
    op.add_column(
        "credit_card",
        sa.Column("is_multicurrency", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("credit_card", sa.Column("secondary_currency_code", sa.String(3), nullable=True))
    op.add_column(
        "credit_card",
        sa.Column("secondary_credit_limit", sa.Numeric(precision=19, scale=4), nullable=True),
    )
    op.add_column(
        "credit_card",
        sa.Column("secondary_available_credit", sa.Numeric(precision=19, scale=4), nullable=True),
    )

    # Drop existing FK constraint on credit_card.account_id and recreate with ON DELETE SET NULL
    op.drop_constraint(
        op.f("fk_credit_card_account_id_financial_account"), "credit_card", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_credit_card_account_id_financial_account"),
        "credit_card",
        "financial_account",
        ["account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Make transaction.account_id nullable
    op.alter_column(
        "transaction",
        "account_id",
        existing_type=UUID(as_uuid=True),
        nullable=True,
        existing_server_default=None,
    )

    # Drop existing FK constraint on transaction.account_id and recreate with ON DELETE SET NULL
    op.drop_constraint(
        op.f("fk_transaction_account_id_financial_account"), "transaction", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_transaction_account_id_financial_account"),
        "transaction",
        "financial_account",
        ["account_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop debit_card table
    op.drop_table("debit_card")

    # Drop multi-currency columns
    op.drop_column("credit_card", "secondary_available_credit")
    op.drop_column("credit_card", "secondary_credit_limit")
    op.drop_column("credit_card", "secondary_currency_code")
    op.drop_column("credit_card", "is_multicurrency")

    # Revert credit_card.account_id to NOT NULL
    op.drop_constraint(
        op.f("fk_credit_card_account_id_financial_account"), "credit_card", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_credit_card_account_id_financial_account"),
        "credit_card",
        "financial_account",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "credit_card",
        "account_id",
        existing_type=UUID(as_uuid=True),
        nullable=False,
        existing_server_default=None,
    )

    # Revert transaction.account_id to NOT NULL
    op.drop_constraint(
        op.f("fk_transaction_account_id_financial_account"), "transaction", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_transaction_account_id_financial_account"),
        "transaction",
        "financial_account",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "transaction",
        "account_id",
        existing_type=UUID(as_uuid=True),
        nullable=False,
        existing_server_default=None,
    )
