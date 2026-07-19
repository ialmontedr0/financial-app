import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

from .financial_account import FinancialAccountModel
from .user_preference import UserPreferenceModel
from .user_profile import UserProfileModel


class UserModel(Base):
    """ORM user model — SQLAlchemy 2.x style."""

    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("user", "admin", "moderator", name="user_role"),
        default="user",
        nullable=False,
        server_default="user",
    )
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    login_count: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    profile: Mapped[UserProfileModel | None] = relationship(
        "UserProfileModel",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    preferences: Mapped[UserPreferenceModel | None] = relationship(
        "UserPreferenceModel",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    accounts: Mapped[list[FinancialAccountModel]] = relationship(
        "FinancialAccountModel",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, email={self.email})>"
