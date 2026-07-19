"""Use case: Create a new wallet."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.wallet_repository import WalletRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateWalletUseCase:
    """Create a new wallet for the authenticated user."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WalletRepository(session)

    async def execute(self, user_id: uuid.UUID, **fields: Any) -> dict:
        """Create a new wallet."""
        from app.domain.wallet.value_objects import WalletType
        from app.middleware.error_handler import ValidationError

        wallet_type = fields.get("wallet_type", "personal")
        try:
            WalletType(wallet_type)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904
        fields["wallet_type"] = wallet_type

        name = fields.get("name")
        if not name or not str(name).strip():
            raise ValidationError("name es requerido")
        fields["name"] = str(name).strip()

        color = fields.get("color")
        if color is not None:
            color_str = str(color).strip()
            if not color_str.startswith("#") or len(color_str) != 7:
                raise ValidationError("color debe ser en formato #RRGGBB")
            fields["color"] = color_str

        wallet = await self._repo.create(user_id, **fields)

        return {
            "id": str(wallet.id),
            "name": wallet.name,
            "description": wallet.description,
            "wallet_type": wallet.wallet_type,
            "status": wallet.status,
            "icon": wallet.icon,
            "color": wallet.color,
            "sort_order": wallet.sort_order,
            "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
        }
