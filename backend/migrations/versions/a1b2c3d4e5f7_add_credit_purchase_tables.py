"""add_credit_purchase_tables

Revision ID: a1b2c3d4e5f7
Revises: ffb27bee88cf
Create Date: 2026-07-29 11:55:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, Sequence[str], None] = "c5ce2bc612fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "credit_purchase",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("store_name", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_price", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("down_payment", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("financed_amount", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("annual_interest_rate", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("installment_count", sa.Integer(), nullable=False),
        sa.Column(
            "installment_frequency",
            sa.Enum(
                "weekly",
                "biweekly",
                "monthly",
                "quarterly",
                "quadrimensual",
                "semestral",
                "annual",
                name="installment_frequency_enum",
            ),
            nullable=False,
        ),
        sa.Column("installment_amount", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("calculation_method", sa.String(length=10), nullable=False),
        sa.Column("total_interest", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("total_paid", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("first_due_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "completed",
                "cancelled",
                "defaulted",
                name="credit_purchase_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_credit_purchase_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credit_purchase")),
    )
    with op.batch_alter_table("credit_purchase", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_credit_purchase_user_id"), ["user_id"], unique=False)
        batch_op.create_index("ix_credit_purchase_user_status", ["user_id", "status"], unique=False)

    op.create_table(
        "credit_purchase_installment",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("purchase_id", sa.UUID(), nullable=False),
        sa.Column("installment_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("principal_portion", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("interest_portion", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("balance_after", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "paid", "late", name="installment_status_enum"),
            nullable=False,
        ),
        sa.Column("paid_at", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["purchase_id"],
            ["credit_purchase.id"],
            name=op.f("fk_credit_purchase_installment_purchase_id_credit_purchase"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credit_purchase_installment")),
    )
    with op.batch_alter_table("credit_purchase_installment", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_credit_purchase_installment_purchase_id"),
            ["purchase_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_installment_purchase_number",
            ["purchase_id", "installment_number"],
            unique=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("credit_purchase_installment", schema=None) as batch_op:
        batch_op.drop_index("ix_installment_purchase_number")
        batch_op.drop_index(batch_op.f("ix_credit_purchase_installment_purchase_id"))
    op.drop_table("credit_purchase_installment")

    with op.batch_alter_table("credit_purchase", schema=None) as batch_op:
        batch_op.drop_index("ix_credit_purchase_user_status")
        batch_op.drop_index(batch_op.f("ix_credit_purchase_user_id"))
    op.drop_table("credit_purchase")

    op.execute("DROP TYPE IF EXISTS installment_status_enum")
    op.execute("DROP TYPE IF EXISTS credit_purchase_status_enum")
    op.execute("DROP TYPE IF EXISTS installment_frequency_enum")
