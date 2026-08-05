from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.infrastructure.repositories.notification_repository import NotificationRepository
from app.infrastructure.repositories.telegram_link_repository import TelegramLinkRepository

logger = structlog.get_logger()
settings = get_settings()

_TELEGRAM_API = "https://api.telegram.org/bot"


class GenerateLinkCodeUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = TelegramLinkRepository(db)

    async def execute(self, user_id: UUID) -> str:
        existing = await self._repo.get_active_by_user(user_id)
        if existing:
            return existing.code
        code = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        await self._repo.create(user_id, code, expires_at)
        return code


class UnlinkTelegramUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._notif_repo = NotificationRepository(db)

    async def execute(self, user_id: UUID) -> None:
        prefs = await self._notif_repo.get_user_preferences(user_id)
        if prefs:
            prefs.telegram_chat_id = None
            prefs.telegram_enabled = False
            await self._notif_repo._db.flush()


class ProcessTelegramUpdateUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._link_repo = TelegramLinkRepository(db)
        self._notif_repo = NotificationRepository(db)

    async def execute(self, update: dict[str, Any]) -> None:
        message = update.get("message")
        if not message:
            return
        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()

        if text.startswith("/start"):
            await self._send_message(
                chat_id,
                "¡Bienvenido a FIP Bot!\n\nPara vincular tu cuenta, ve a "
                "Preferencias de Notificacion en la plataforma, haz clic en "
                '"Vincular Telegram" y envia el codigo que aparezca usando:\n'
                "/link <codigo>\n\n"
                "Ejemplo: /link 482917",
            )
            return

        if text.startswith("/link"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                await self._send_message(chat_id, "Usa: /link <codigo>\nEjemplo: /link 482917")
                return
            code = parts[1].strip()
            link = await self._link_repo.get_by_code(code)
            if not link:
                await self._send_message(chat_id, "Codigo invalido. Verifica e intenta de nuevo.")
                return
            if link.is_used:
                await self._send_message(chat_id, "Este codigo ya fue usado.")
                return
            if link.expires_at.replace(tzinfo=None) < datetime.utcnow():
                await self._send_message(
                    chat_id, "El codigo ha expirado. Genera uno nuevo en la plataforma."
                )
                return
            await self._link_repo.mark_used(link)
            prefs = await self._notif_repo.get_user_preferences(link.user_id)
            if prefs:
                prefs.telegram_chat_id = str(chat_id)
                prefs.telegram_enabled = True
                await self._notif_repo._db.flush()
            else:
                await self._notif_repo.upsert_preferences(
                    link.user_id,
                    {"telegram_chat_id": str(chat_id), "telegram_enabled": True},
                )
            await self._send_message(
                chat_id,
                "¡Cuenta vinculada exitosamente! A partir de ahora recibiras "
                "notificaciones de FIP aqui.",
            )
            logger.info("telegram_account_linked", user_id=str(link.user_id), chat_id=chat_id)
            return

        if text.startswith("/unlink"):
            from sqlalchemy import select
            from app.infrastructure.models.notification_preference import (
                NotificationPreferenceModel,
            )

            result = await self._notif_repo._db.execute(
                select(NotificationPreferenceModel).where(
                    NotificationPreferenceModel.telegram_chat_id == str(chat_id)
                )
            )
            prefs = result.scalar_one_or_none()
            if prefs:
                prefs.telegram_chat_id = None
                prefs.telegram_enabled = False
                await self._notif_repo._db.flush()
                await self._send_message(
                    chat_id, "Cuenta desvinculada. Ya no recibiras notificaciones aqui."
                )
                logger.info("telegram_account_unlinked", chat_id=chat_id)
            else:
                await self._send_message(chat_id, "No hay ninguna cuenta vinculada a este chat.")
            return

        await self._send_message(
            chat_id,
            "Comandos disponibles:\n"
            "/start - Informacion\n"
            "/link <codigo> - Vincular tu cuenta de FIP\n"
            "/unlink - Desvincular tu cuenta de FIP",
        )

    async def _send_message(self, chat_id: int | str, text: str) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{_TELEGRAM_API}{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                await client.post(
                    url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
                )
        except Exception as exc:
            logger.warning("telegram_webhook_reply_failed", chat_id=chat_id, error=str(exc))
