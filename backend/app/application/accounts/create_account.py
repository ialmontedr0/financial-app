"""Use case: Create a new financial account."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.account_repository import AccountRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateAccountUseCase:
    """Create a new financial account for the authenticated user."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AccountRepository(session)

    async def execute(self, user_id: uuid.UUID, **fields: Any) -> dict:
        """Create a new account."""
        from app.domain.accounts.value_objects import AccountType
        from app.domain.users.value_objects import CurrencyCode
        from app.middleware.error_handler import ValidationError

        account_type = fields.get("account_type")
        if not account_type:
            raise ValidationError("account_type es requerido")

        try:
            AccountType(account_type)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904

        currency_code = fields.get("currency_code", "DOP")
        try:
            CurrencyCode(currency_code)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904
        fields["currency_code"] = currency_code.upper()

        name = fields.get("name")
        if not name or not str(name).strip():
            raise ValidationError("name es requerido")
        fields["name"] = str(name).strip()

        initial_balance = fields.get("initial_balance", 0)
        try:
            initial_balance = str(initial_balance)
        except (ValueError, TypeError):
            raise ValidationError("initial_balance invalido")  # noqa: B904

        fields["initial_balance"] = initial_balance
        fields["balance"] = initial_balance

        last4 = fields.get("account_number_last4")
        if last4 is not None:
            last4_str = str(last4).strip()
            if not last4_str.isdigit() or len(last4_str) != 4:
                raise ValidationError("account_number_last4 debe ser exactamente 4 digitos")
            fields["account_number_last4"] = last4_str

        color = fields.get("color")
        if color is not None:
            color_str = str(color).strip()
            if not color_str.startswith("#") or len(color_str) != 7:
                raise ValidationError("color debe ser en formato #RRGGBB")
            fields["color"] = color_str

        account = await self._repo.create(user_id, **fields)

        return {
            "id": str(account.id),
            "name": account.name,
            "account_type": account.account_type,
            "currency_code": account.currency_code,
            "balance": str(account.balance),
            "initial_balance": str(account.initial_balance),
            "institution": account.institution,
            "status": account.status,
            "include_in_net_worth": account.include_in_net_worth,
            "created_at": account.created_at.isoformat() if account.created_at else None,
        }
