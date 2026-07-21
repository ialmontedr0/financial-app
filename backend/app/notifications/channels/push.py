from __future__ import annotations

from app.notifications.channels.base import BaseChannel, NotificationMessage, NotificationResult


class PushChannel(BaseChannel):
    async def send(self, message: NotificationMessage) -> NotificationResult:
        return NotificationResult(
            success=True, channel="push", message_id=f"push_{message.user_id}"
        )

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "push"
