"""Use case: Update a financial account."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.account_repository import AccountRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

ALLOWED_UPDATE_FIELDS = {
    "name",
    "institution",
    "account_number_last4",
    "icon",
    "color",
    "notes",
    "include_in_net_worth",
    "include_in_totals",
    "sort_order",
    "status",
}


class UpdateAccountUseCase:
    """Update a financial account (partial update)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AccountRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        **fields: Any,
    ) -> dict:
        """Update account fields."""
        from app.middleware.error_handler import ConflictError, NotFoundError, ValidationError

        expected_version = fields.pop("version", None)

        invalid = set(fields.keys()) - ALLOWED_UPDATE_FIELDS
        if invalid:
            raise ValidationError(f"Campos no permitidos para actualizacion: {', '.join(invalid)}")

        if "name" in fields:
            name = str(fields["name"]).strip()
            if not name:
                raise ValidationError("name no puede estar vacio")
            fields["name"] = name

        if "status" in fields:
            from app.domain.accounts.value_objects import AccountStatus

            try:
                AccountStatus(fields["status"])
            except ValueError as e:
                raise ValidationError(str(e))  # noqa: B904

        if "account_number_last4" in fields and fields["account_number_last4"] is not None:
            last4 = str(fields["account_number_last4"]).strip()
            if not last4.isdigit() or len(last4) != 4:
                raise ValidationError("account_number_last4 debe ser exactamente 4 digitos")
            fields["account_number_last4"] = last4

        if "color" in fields and fields["color"] is not None:
            color = str(fields["color"]).strip()
            if not color.startswith("#") or len(color) != 7:
                raise ValidationError("color debe ser en formato #RRGGBB")
            fields["color"] = color

        account = await self._repo.get_by_id(account_id, user_id)
        if account is None:
            raise NotFoundError("Account")

        # Optimistic locking: reject stale writes only when the client sends a version
        if expected_version is not None and account.version != int(expected_version):
            raise ConflictError(
                "Registro modificado por otro usuario, recargue e intentelo de nuevo"
            )

        updated = await self._repo.update(account_id, user_id, **fields)
        if updated is None:
            raise NotFoundError("Account")

        updated.version += 1
        await self._session.flush()
        await self._session.refresh(updated)

        return {
            "id": str(updated.id),
            "name": updated.name,
            "account_type": updated.account_type,
            "status": updated.status,
            "currency_code": updated.currency_code,
            "balance": str(updated.balance),
            "institution": updated.institution,
            "account_number_last4": updated.account_number_last4,
            "icon": updated.icon,
            "color": updated.color,
            "notes": updated.notes,
            "include_in_net_worth": updated.include_in_net_worth,
            "include_in_totals": updated.include_in_totals,
            "sort_order": updated.sort_order,
            "version": updated.version,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
