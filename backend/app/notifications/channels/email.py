from __future__ import annotations

from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import get_settings
from app.infrastructure.email.email_service import EmailService
from app.notifications.channels.base import BaseChannel, NotificationMessage, NotificationResult

logger = structlog.get_logger()
settings = get_settings()

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


class EmailChannel(BaseChannel):
    def __init__(self) -> None:
        self._email_service = EmailService()
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=select_autoescape(["html"]),
        )

    async def send(self, message: NotificationMessage) -> NotificationResult:
        try:
            to_email = message.data.get("email")
            if not to_email:
                return NotificationResult(
                    success=False, channel="email", error="No email address provided"
                )

            template_name = f"{message.type}.html"
            try:
                template = self._env.get_template(template_name)
            except Exception:
                template = self._env.get_template("test_notification.html")

            html = template.render(
                title=message.title,
                body=message.body,
                **(message.template_vars or {}),
            )

            await self._email_service._send_email(
                to_email=to_email, subject=message.title, html_body=html
            )
            return NotificationResult(
                success=True, channel="email", message_id=f"email_{message.user_id}"
            )
        except Exception as exc:
            logger.exception("email_channel_send_failed")
            return NotificationResult(success=False, channel="email", error=str(exc))

    def is_configured(self) -> bool:
        return bool(settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD)

    def get_name(self) -> str:
        return "email"
