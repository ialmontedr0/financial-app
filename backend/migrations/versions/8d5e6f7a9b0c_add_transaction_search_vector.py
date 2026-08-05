"""add transaction search vector

Revision ID: 8d5e6f7a9b0c
Revises: 7c4d5e6f8a9b
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "8d5e6f7a9b0c"
down_revision: Union[str, None] = "7c4d5e6f8a9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE transaction ADD COLUMN search_vector tsvector"
        " GENERATED ALWAYS AS ("
        " to_tsvector('spanish', coalesce(description, '') || ' ' || coalesce(notes, ''))"
        ") STORED;"
    )
    op.execute(
        "CREATE INDEX ix_transaction_search_vector ON transaction USING GIN (search_vector);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_transaction_search_vector;")
    op.execute("ALTER TABLE transaction DROP COLUMN IF EXISTS search_vector;")
