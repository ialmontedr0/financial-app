"""Use case: Update a wallet."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.wallet_repository import WalletRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

ALLOWED_UPDATE_FIELDS = {
    "name",
    "description",
    "wallet_type",
    "icon",
    "color",
    "sort_order",
    "status",
}


class UpdateWalletUseCase:
    """Update a wallet (partial update)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WalletRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        wallet_id: uuid.UUID,
        **fields: Any,
    ) -> dict:
        """Update wallet fields."""
        from app.domain.wallet.value_objects import WalletStatus, WalletType
        from app.middleware.error_handler import NotFoundError, ValidationError

        invalid = set(fields.keys()) - ALLOWED_UPDATE_FIELDS
        if invalid:
            raise ValidationError(
                f"Campos no permitidos para actualizacion: {', '.join(invalid)}"
            )

        if "name" in fields:
            name = str(fields["name"]).strip()
            if not name:
                raise ValidationError("name no puede estar vacio")
            fields["name"] = name

        if "wallet_type" in fields:
            try:
                WalletType(fields["wallet_type"])
            except ValueError as e:
                raise ValidationError(str(e))  # noqa: B904

        if "status" in fields:
            try:
                WalletStatus(fields["status"])
            except ValueError as e:
                raise ValidationError(str(e))  # noqa: B904

        if "color" in fields and fields["color"] is not None:
            color = str(fields["color"]).strip()
            if not color.startswith("#") or len(color) != 7:
                raise ValidationError("color debe ser en formato #RRGGBB")
            fields["color"] = color

        wallet = await self._repo.update(wallet_id, user_id, **fields)
        if wallet is None:
            raise NotFoundError("Wallet")

        return {
            "id": str(wallet.id),
            "name": wallet.name,
            "description": wallet.description,
            "wallet_type": wallet.wallet_type,
            "status": wallet.status,
            "icon": wallet.icon,
            "color": wallet.color,
            "sort_order": wallet.sort_order,
            "updated_at": wallet.updated_at.isoformat() if wallet.updated_at else None,
        }
