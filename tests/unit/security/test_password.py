import pytest

from app.infrastructure.security.password_hasher import PasswordHasher


@pytest.mark.unit
class TestPasswordHasher:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        hashed = PasswordHasher.hash_password("mypassword")
        assert isinstance(hashed, str)
        assert hashed != "mypassword"
        assert hashed.startswith("$2")

    def test_verify_correct_password(self):
        password = "secure_password_123"
        hashed = PasswordHasher.hash_password(password)
        assert PasswordHasher.verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        hashed = PasswordHasher.hash_password("correct_password")
        assert PasswordHasher.verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        hashed1 = PasswordHasher.hash_password("same_password")
        hashed2 = PasswordHasher.hash_password("same_password")
        # bcrypt uses random salt, so hashes should differ
        assert hashed1 != hashed2

    def test_needs_update_false(self):
        hashed = PasswordHasher.hash_password("password")
        assert PasswordHasher.needs_update(hashed) is False

    def test_verify_empty_password(self):
        hashed = PasswordHasher.hash_password("password")
        assert PasswordHasher.verify_password("", hashed) is False

    def test_hash_empty_password(self):
        # Should still produce a valid hash (application should validate before hashing)
        hashed = PasswordHasher.hash_password("")
        assert isinstance(hashed, str)
        assert PasswordHasher.verify_password("", hashed) is True
