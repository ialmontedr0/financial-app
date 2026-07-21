from __future__ import annotations

import httpx
import structlog

from app.core.config import get_settings
from app.notifications.channels.base import BaseChannel, NotificationMessage, NotificationResult

logger = structlog.get_logger()
settings = get_settings()

_TYPE_COLORS: dict[str, int] = {
    "transaction_alert": 0x3498db,
    "budget_warning": 0xE74C3C,
    "goal_completed": 0x2ECC71,
    "bill_due": 0xF39C12,
    "anomaly_detected": 0x9B59B6,
    "automation_executed": 0x1ABC9C,
    "security_alert": 0xE74C3C,
    "system": 0x95A5A6,
    "marketing": 0x3498DB,
}


class DiscordChannel(BaseChannel):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, message: NotificationMessage) -> NotificationResult:
        webhook_url = message.data.get("discord_webhook_url") or settings.DISCORD_WEBHOOK_URL
        if not webhook_url:
            return NotificationResult(
                success=False, channel="discord", error="Discord webhook URL not configured"
            )

        try:
            embed = {
                "title": message.title,
                "description": message.body,
                "color": _TYPE_COLORS.get(message.type, 0x95A5A6),
            }
            resp = await self._client.post(webhook_url, json={"embeds": [embed]})
            resp.raise_for_status()
            return NotificationResult(
                success=True,
                channel="discord",
                message_id=resp.headers.get("X-Message-Id"),
            )
        except Exception as exc:
            logger.exception("discord_channel_send_failed")
            return NotificationResult(success=False, channel="discord", error=str(exc))

    def is_configured(self) -> bool:
        return bool(settings.DISCORD_WEBHOOK_URL)

    def get_name(self) -> str:
        return "discord"
