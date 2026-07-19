import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class UserRole(str, Enum):  # noqa: UP042
    """Roles de usuario para RBAC."""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


@dataclass(frozen=True)
class Email:
    """Validated email value object."""

    value: str

    def __post_init__(self) -> None:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, self.value):
            raise ValueError(f"Formato de correo invalido: {self.value}")

    def __str__(self) -> str:
        return self.value.lower()

    @property
    def normalized(self) -> str:
        return self.value.lower().strip()


@dataclass(frozen=True)
class PasswordHash:
    """Password hash value object (nunca almacena texto plano.)"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Hash de contrasena no puede estar vacio")


@dataclass(frozen=True)
class TokenPair:
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int = 900

    def to_dict(self) -> dict[str, str | int]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }


@dataclass(frozen=True)
class MFASecret:
    """MFA Secret value object."""

    secret: str
    uri: str
    qr_code_base64: str = ""


@dataclass(frozen=True)
class DeviceInfo:
    """Device fingerprint for session tracking."""

    user_agent: str = "unknown"
    ip_address: str = "0.0.0.0"  # noqa: S104

    def __str__(self) -> str:
        return f"{self.user_agent[:50]}|{self.ip_address}"


@dataclass
class SessionData:
    """Session data stored in Redis."""

    user_id: str
    jti: str
    device_info: DeviceInfo
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))  # noqa: UP017
    expires_at: datetime | None = None
    is_active: bool = True
