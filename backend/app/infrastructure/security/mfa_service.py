import base64
import io

import pyotp
import qrcode
import qrcode.image.svg
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class MFAService:
    """Servicio para TOTP-based autenticacion multifactor."""

    @staticmethod
    def generate_secret() -> str:
        """Genera una clave secreta MFA.

        Returns:
            str
        """
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, email: str) -> str:
        """Genera una URI TOTP para aplicaciones de autenticador."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=settings.MFA_ISSUER_NAME)

    @staticmethod
    def verify_code(
        secret: str,
        code: str,
    ) -> bool:
        """Verifica un codico TOTP contra el secreto.

        Permite una ventana 1-paso para clock drift.

        Args:
            secret (str): _description_
            code (str): _description_

        Returns:
            bool: _description_
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)

    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """Genera un codigo QR como una imagen PNG base64-encoded.

        Args:
            uri (str): _description_

        Returns:
            str: _description_
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )

        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        logger.info("mfa_qr_generated")
        return img_base64

    @staticmethod
    def generate_mfa_setup(email: str) -> tuple[str, str, str]:
        """Generar un paquete de configuracion MFA completo.

        Args:
            email (str): _description_

        Returns:
            tuple[str, str, str]: [secret, totp_uri, qr_code_base64]
        """
        secret = MFAService.generate_secret()
        uri = MFAService.get_totp_uri(secret, email)
        qr_b64 = MFAService.generate_qr_code(uri)
        return secret, uri, qr_b64
