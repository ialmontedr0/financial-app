from __future__ import annotations

from app.notifications.channels.base import BaseChannel, NotificationMessage, NotificationResult


class PushChannel(BaseChannel):
    async def send(self, message: NotificationMessage) -> NotificationResult:
        return NotificationResult(
            success=True, channel="push", message_id=f"push_{message.user_id}"
        )

    def is_configured(self) -> bool:
        """Push requires a real delivery backend (VAPID/Web Push).

        Sin configuración de push instalada, devuelve False para que el canal
        se omita en vez de registrar envíos falsos. (Feature B añade el backend.)
        """
        return False

    def get_name(self) -> str:
        return "push"
