"""Transaction notification helpers.

Emits notifications synchronously whenever a transaction is created,
updated or deleted so delivery does not depend on the background worker.
Respects the user's channel and per-type notification preferences.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

_TRANSACTION_ALERT_TYPE = "transaction_alert"


async def emit_transaction_notification(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    transaction_id: uuid.UUID,
    account_id: uuid.UUID | None,
    amount: object,
    currency_code: str,
    action: str,
) -> bool:
    """Persist an in-app notification for a transaction lifecycle event.

    ``action`` is one of ``"created"``, ``"updated"`` or ``"deleted"``.
    Returns True when the notification was emitted.
    """
    from app.infrastructure.repositories.account_repository import AccountRepository
    from app.notifications.service import NotificationService

    account_name = ""
    if account_id:
        account = await AccountRepository(session).get_by_id(account_id, user_id)
        account_name = account.name if account else ""

    title_tpl, body_tpl, has_link = _config(action)
    body = body_tpl.format(
        amount=amount,
        currency=currency_code,
        account=account_name or "tu cuenta",
    )

    data: dict[str, object] = {"transaction_id": str(transaction_id)}
    if account_id:
        data["account_id"] = str(account_id)
    if has_link:
        data["link"] = f"/transactions/{transaction_id}"

    service = NotificationService(session)
    await service.send(
        user_id=user_id,
        type=_TRANSACTION_ALERT_TYPE,
        title=title_tpl,
        body=body,
        data=data,
    )
    logger.info(
        "transaction_notification",
        user_id=str(user_id),
        transaction_id=str(transaction_id),
        action=action,
    )
    return True


def _config(action: str) -> tuple[str, str, bool]:
    if action == "created":
        return (
            "Transacción registrada",
            "Transaccion de {amount} {currency} registrada en {account}",
            True,
        )
    if action == "updated":
        return (
            "Transacción actualizada",
            "Transaccion de {amount} {currency} actualizada en {account}",
            True,
        )
    return (
        "Transacción eliminada",
        "Transaccion de {amount} {currency} eliminada de {account}",
        False,
    )
