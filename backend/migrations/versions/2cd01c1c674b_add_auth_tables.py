"""add_auth_tables

Revision ID: 2cd01c1c674b
Revises: 6a40f8aada96
Create Date: 2026-07-19 10:40:47.853736

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2cd01c1c674b"
down_revision: str | Sequence[str] | None = "6a40f8aada96"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Clean up any orphaned enum types from previous failed migrations
    op.execute("DROP TYPE IF EXISTS user_role CASCADE")
    op.execute("DROP TYPE IF EXISTS verification_purpose CASCADE")

    # Create user_role BEFORE batch_alter_table (batch ops don't auto-create enums)
    user_role = sa.Enum("user", "admin", "moderator", name="user_role")
    user_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "email_verification",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column(
            "purpose",
            sa.Enum(
                "registration", "password_reset", "email_change",
                name="verification_purpose",
            ),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_email_verification_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_verification")),
    )
    with op.batch_alter_table("email_verification", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_email_verification_token"), ["token"], unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_email_verification_user_id"), ["user_id"], unique=False,
        )

    op.create_table(
        "user_session",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("device_info", sa.String(length=500), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=False),
        sa.Column("refresh_token_jti", sa.String(length=255), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_user_session_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_session")),
    )
    with op.batch_alter_table("user_session", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_user_session_refresh_token_jti"),
            ["refresh_token_jti"],
            unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_user_session_user_id"), ["user_id"], unique=False,
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                sa.Enum("user", "admin", "moderator", name="user_role"),
                server_default="user",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("phone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("avatar_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("mfa_secret", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        )
        batch_op.add_column(sa.Column("login_count", sa.Integer(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("login_count")
        batch_op.drop_column("last_login_at")
        batch_op.drop_column("mfa_secret")
        batch_op.drop_column("avatar_url")
        batch_op.drop_column("phone")
        batch_op.drop_column("role")

    with op.batch_alter_table("user_session", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_session_user_id"))
        batch_op.drop_index(batch_op.f("ix_user_session_refresh_token_jti"))

    op.drop_table("user_session")

    with op.batch_alter_table("email_verification", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_email_verification_user_id"))
        batch_op.drop_index(batch_op.f("ix_email_verification_token"))

    op.drop_table("email_verification")

    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="verification_purpose").drop(op.get_bind(), checkfirst=True)
