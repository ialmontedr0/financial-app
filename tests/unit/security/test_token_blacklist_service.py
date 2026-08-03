"""Tests for the JWT token blacklist service."""

import pytest

from app.infrastructure.cache.redis import redis_client
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.token_blacklist_service import (
    ACCESS_BLACKLIST_PREFIX,
    TokenBlacklistService,
)


@pytest.mark.unit
class TestTokenBlacklistService:
    """Tests for TokenBlacklistService (Redis-backed revocation)."""

    async def test_blacklist_token_and_detect(self):
        token = JWTService.create_access_token("user-123")
        payload = JWTService.decode_token(token)
        jti = payload["jti"]

        assert await TokenBlacklistService.is_blacklisted(jti) is False

        assert await TokenBlacklistService.blacklist_token(token) is True
        assert await TokenBlacklistService.is_blacklisted(jti) is True

    async def test_blacklist_refresh_token(self):
        token = JWTService.create_refresh_token("user-123")
        payload = JWTService.decode_token(token)
        jti = payload["jti"]

        assert await TokenBlacklistService.blacklist_token(token) is True
        assert await TokenBlacklistService.is_blacklisted(jti, kind="refresh") is True
        assert await TokenBlacklistService.is_blacklisted(jti, kind="access") is False

    async def test_blacklist_invalid_token(self):
        assert await TokenBlacklistService.blacklist_token("not-a-real-token") is False

    async def test_blacklist_access_jti(self):
        token = JWTService.create_access_token("user-123")
        payload = JWTService.decode_token(token)
        jti = payload["jti"]
        exp = payload["exp"]

        assert await TokenBlacklistService.is_blacklisted(jti) is False
        assert await TokenBlacklistService.blacklist_access_jti(jti, exp) is True
        assert await TokenBlacklistService.is_blacklisted(jti) is True

    async def test_expired_token_ttl_is_zero(self):
        token = JWTService.create_access_token("user-123")
        payload = JWTService.decode_token(token)
        jti = payload["jti"]

        assert await TokenBlacklistService.blacklist_access_jti(jti, 0) is False
        assert await TokenBlacklistService.is_blacklisted(jti) is False

    async def test_cleanup(self):
        key = f"{ACCESS_BLACKLIST_PREFIX}:cleanup-jti"
        await redis_client.delete(key)
