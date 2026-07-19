from __future__ import annotations

import bcrypt


class PasswordHasher:
    """Service for hashing and verifying passwords with bcrypt."""

    _ROUNDS = 12

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain-text password."""
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=PasswordHasher._ROUNDS)
        return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain-text password against a bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    @staticmethod
    def needs_update(hashed_password: str) -> bool:
        """Check if the hash was created with an older work factor."""
        try:
            stored_rounds = hashed_password.split("$")[2]
            return int(stored_rounds) < PasswordHasher._ROUNDS
        except (IndexError, ValueError):
            return True
