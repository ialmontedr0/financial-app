from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.notification_preference import NotificationPreferenceModel
from app.infrastructure.repositories.notification_repository import NotificationRepository
from app.notifications.channels.base import BaseChannel, NotificationMessage, NotificationResult
from app.notifications.channels.discord import DiscordChannel
from app.notifications.channels.email import EmailChannel
from app.notifications.channels.push import PushChannel
from app.notifications.channels.telegram import TelegramChannel
from app.notifications.channels.webhook import WebhookChannel

logger = structlog.get_logger()

_ALL_CHANNELS = ("email", "push", "telegram", "discord", "webhook")


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)
        self._channels: dict[str, BaseChannel] = {
            "email": EmailChannel(),
            "push": PushChannel(),
            "telegram": TelegramChannel(),
            "discord": DiscordChannel(),
            "webhook": WebhookChannel(),
        }

    @property
    def repo(self) -> NotificationRepository:
        return self._repo

    async def send(
        self,
        *,
        user_id: UUID,
        type: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        channels: list[str] | None = None,
    ) -> list[NotificationResult]:
        preferences = await self._repo.get_user_preferences(user_id)
        if not preferences:
            preferences = await self._repo.upsert_preferences(user_id, {})

        enabled = self._resolve_channels(preferences, channels)
        base_data = data or {}
        results: list[NotificationResult] = []

        for ch_name in enabled:
            channel = self._channels.get(ch_name)
            if not channel or not channel.is_configured():
                continue
            if not self._type_enabled(preferences, ch_name, type):
                continue

            ch_data = self._enrich_channel_data(ch_name, base_data, preferences)
            msg = NotificationMessage(
                user_id=user_id,
                channel=ch_name,
                type=type,
                title=title,
                body=body,
                data=ch_data,
                template_vars=base_data,
            )

            try:
                result = await channel.send(msg)
            except Exception as exc:
                logger.exception("notification_channel_error", channel=ch_name)
                result = NotificationResult(success=False, channel=ch_name, error=str(exc))

            results.append(result)

            await self._repo.create(
                user_id=user_id,
                channel=ch_name,
                type=type,
                title=title,
                body=body,
                data=base_data,
                is_sent=result.success,
                sent_at=None,
            )

        return results

    def _resolve_channels(
        self, prefs: NotificationPreferenceModel, requested: list[str] | None
    ) -> tuple[str, ...]:
        if requested:
            return tuple(c for c in requested if c in _ALL_CHANNELS)
        enabled = []
        for ch in _ALL_CHANNELS:
            if getattr(prefs, f"{ch}_enabled", False):
                enabled.append(ch)
        return tuple(enabled)

    @staticmethod
    def _type_enabled(
        prefs: NotificationPreferenceModel, channel: str, type_: str
    ) -> bool:
        types_dict = getattr(prefs, f"{channel}_types", None)
        if types_dict is None:
            return True
        return types_dict.get(type_, True)

    @staticmethod
    def _enrich_channel_data(
        channel: str, data: dict[str, Any], prefs: NotificationPreferenceModel
    ) -> dict[str, Any]:
        enriched = dict(data)
        if channel == "telegram":
            enriched.setdefault("telegram_chat_id", prefs.telegram_chat_id)
        elif channel == "discord":
            enriched.setdefault("discord_webhook_url", prefs.discord_webhook_url)
        elif channel == "webhook":
            enriched.setdefault("webhook_url", prefs.webhook_url)
            enriched.setdefault("webhook_secret", prefs.webhook_secret)
        return enriched
