from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class UserRegisteredEvent:
    """Se emite cuando se registra un nuevo usuario."""

    event_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    email: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "user.registered"


@dataclass(frozen=True)
class UserLoggedInEvent:
    """Se emite cuando se logea un usuario."""

    event_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    email: str = ""
    ip_address: str = ""
    user_agent: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "user.logged_in"


@dataclass(frozen=True)
class PasswordResetRequestedEvent:
    """Se emite cunaod se solicita un restablecimiento de contrasena."""

    event_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    email: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "password.reset_requested"


@dataclass(frozen=True)
class PasswordResetEvent:
    """Se emite cuando una contrasena es restablecida exitosamente."""

    event_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    email: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "password.reset"


@dataclass(frozen=True)
class EmailVerifiedEvent:
    """Se emite cuando un usuario verifica su email."""

    event_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    email: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "email.verified"


@dataclass(frozen=True)
class MFAEnabledEvent:
    """Se emite cuando MFA es activado por un usuario."""

    event_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "mfa.enabled"


@dataclass(frozen=True)
class MFADisabledEvent:
    """Se emite cuando MFA es desactivado por un usuario."""

    event_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "mfa.disabled"


@dataclass(frozen=True)
class UserSessionRevokedEvent:
    """Se emite cuando la sesion de un usuario es revocada."""

    event_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    session_jti: str = ""
    revoked_all: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "session.revoked"
