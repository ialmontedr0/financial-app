from pathlib import Path

import aiosmtplib
import structlog
from jinja2 import Environment, FileSystemLoader

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Path to email templates
_template_dir = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_template_dir)), autoescape=True)


class EmailService:
    """Async email service using aiosmtplib + Jinja2."""

    @staticmethod
    async def _send_email(
        to_email: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Send an email via SMTP.

        In development mode, we log the email instead of sending it.
        """
        if settings.DEBUG or not settings.EMAIL_USERNAME:
            logger.info(
                "email_sent_dev_mode",
                to=to_email,
                subject=subject,
                body_preview=html_body[:200],
            )
            return

        message = f"""From: {settings.EMAIL_FROM}
To: {to_email}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8

{html_body}"""

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_USERNAME,
                password=settings.EMAIL_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
            )
            logger.info("email_sent_successfully", to=to_email, subject=subject)
        except aiosmtplib.SMTPException as exc:
            logger.error("email_send_failed", to=to_email, error=str(exc))
            raise

    @staticmethod
    async def send_verification_email(to_email: str, token: str, user_name: str = "") -> None:
        """Send an email verification link."""
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        template = _jinja_env.get_template("verification.html")
        html_body = template.render(
            user_name=user_name or to_email.split("@")[0],
            verify_url=verify_url,
            app_name=settings.APP_NAME,
        )
        await EmailService._send_email(
            to_email=to_email,
            subject=f"Verifica tu email en {settings.APP_NAME}",
            html_body=html_body,
        )

    @staticmethod
    async def send_password_reset_email(to_email: str, token: str, user_name: str = "") -> None:
        """Send a password reset link."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        template = _jinja_env.get_template("password_reset.html")
        html_body = template.render(
            user_name=user_name or to_email.split("@")[0],
            reset_url=reset_url,
            app_name=settings.APP_NAME,
            expires_hours=24,
        )
        await EmailService._send_email(
            to_email=to_email,
            subject=f"Restablece tu contrasena en {settings.APP_NAME}",
            html_body=html_body,
        )

    @staticmethod
    async def send_mfa_code(to_email: str, code: str) -> None:
        """Send a TOTP MFA code via email (backup method)."""
        html_body = f"""
        <html>
        <body>
            <h2>Codigo de Verificacion</h2>
            <p>Tu codigo de verificacion es:</p>
            <h1 style="font-size: 32px; letter-spacing: 8px; color: #2563eb;">{code}</h1>
            <p>Este codigo expira en 5 minutos.</p>
            <p>Si no solicitaste este codigo, ignora este mensaje.</p>
        </body>
        </html>
        """
        await EmailService._send_email(
            to_email=to_email,
            subject="Tu codigo de verificacion",
            html_body=html_body,
        )
