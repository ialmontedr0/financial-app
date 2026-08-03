"""enforce ON DELETE CASCADE on telegram_link_code.user_id

Revision ID: b0c1d2e3f4a5
Revises: 9a7c2f3e5d1b
Create Date: 2026-08-01 16:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b0c1d2e3f4a5"
down_revision: str | None = "9a7c2f3e5d1b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_telegram_link_code_user_id_user",
        "telegram_link_code",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_telegram_link_code_user_id_user",
        "telegram_link_code",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_telegram_link_code_user_id_user",
        "telegram_link_code",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_telegram_link_code_user_id_user",
        "telegram_link_code",
        "user",
        ["user_id"],
        ["id"],
    )
