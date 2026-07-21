from __future__ import annotations

import hashlib
import hmac
import json

import httpx
import structlog

from app.notifications.channels.base import BaseChannel, NotificationMessage, NotificationResult

logger = structlog.get_logger()


class WebhookChannel(BaseChannel):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, message: NotificationMessage) -> NotificationResult:
        webhook_url = message.data.get("webhook_url")
        webhook_secret = message.data.get("webhook_secret", "")

        if not webhook_url:
            return NotificationResult(
                success=False, channel="webhook", error="No webhook_url provided"
            )

        try:
            payload = {
                "type": message.type,
                "title": message.title,
                "body": message.body,
                "data": message.data,
                "user_id": str(message.user_id),
            }

            headers: dict[str, str] = {"Content-Type": "application/json"}
            if webhook_secret:
                sig = hmac.new(
                    webhook_secret.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={sig}"

            resp = await self._client.post(webhook_url, json=payload, headers=headers)
            resp.raise_for_status()
            return NotificationResult(
                success=True,
                channel="webhook",
                metadata={"status_code": resp.status_code},
            )
        except Exception as exc:
            logger.exception("webhook_channel_send_failed")
            return NotificationResult(success=False, channel="webhook", error=str(exc))

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "webhook"
