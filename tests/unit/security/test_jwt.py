
import pytest

from app.infrastructure.security.jwt_service import JWTService


@pytest.mark.unit
class TestJWTService:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        token = JWTService.create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        token = JWTService.create_refresh_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        token = JWTService.create_access_token("user-123")
        payload = JWTService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_decode_refresh_token(self):
        token = JWTService.create_refresh_token("user-456")
        payload = JWTService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_verify_access_token(self):
        token = JWTService.create_access_token("user-123")
        payload = JWTService.verify_token(token, expected_type="access")
        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_verify_refresh_token(self):
        token = JWTService.create_refresh_token("user-123")
        payload = JWTService.verify_token(token, expected_type="refresh")
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_verify_wrong_type_rejected(self):
        token = JWTService.create_access_token("user-123")
        payload = JWTService.verify_token(token, expected_type="refresh")
        assert payload is None

    def test_decode_invalid_token(self):
        payload = JWTService.decode_token("invalid.token.value")
        assert payload is None

    def test_decode_empty_token(self):
        payload = JWTService.decode_token("")
        assert payload is None

    def test_additional_claims(self):
        token = JWTService.create_access_token("user-123", additional_claims={"mfa_pending": True})
        payload = JWTService.decode_token(token)
        assert payload is not None
        assert payload["mfa_pending"] is True

    def test_token_jti_is_unique(self):
        token1 = JWTService.create_access_token("user-123")
        token2 = JWTService.create_access_token("user-123")
        payload1 = JWTService.decode_token(token1)
        payload2 = JWTService.decode_token(token2)
        assert payload1["jti"] != payload2["jti"]
