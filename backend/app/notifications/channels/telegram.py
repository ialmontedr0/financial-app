from __future__ import annotations

import httpx
import structlog

from app.core.config import get_settings
from app.notifications.channels.base import BaseChannel, NotificationMessage, NotificationResult

logger = structlog.get_logger()
settings = get_settings()

_TELEGRAM_API = "https://api.telegram.org/bot"


class TelegramChannel(BaseChannel):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, message: NotificationMessage) -> NotificationResult:
        if not settings.TELEGRAM_BOT_TOKEN:
            return NotificationResult(
                success=False, channel="telegram", error="Telegram bot token not configured"
            )

        chat_id = message.data.get("telegram_chat_id")
        if not chat_id:
            return NotificationResult(
                success=False, channel="telegram", error="No telegram_chat_id provided"
            )

        try:
            url = f"{_TELEGRAM_API}{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": f"*{message.title}*\n\n{message.body}",
                "parse_mode": "Markdown",
            }
            resp = await self._client.post(url, json=payload)
            resp.raise_for_status()

            msg_id = str(resp.json().get("result", {}).get("message_id", ""))
            return NotificationResult(
                success=True,
                channel="telegram",
                message_id=msg_id,
                metadata={"chat_id": chat_id},
            )
        except Exception as exc:
            logger.exception("telegram_channel_send_failed")
            return NotificationResult(success=False, channel="telegram", error=str(exc))

    def is_configured(self) -> bool:
        return bool(settings.TELEGRAM_BOT_TOKEN)

    def get_name(self) -> str:
        return "telegram"
