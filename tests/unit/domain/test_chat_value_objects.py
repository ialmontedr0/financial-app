"""Unit tests for chat domain value objects."""

from app.domain.chat.value_objects import (
    VALID_CHAT_TYPES,
    VALID_ROLES,
    ChatRole,
    ChatType,
)


class TestChatValueObjects:
    def test_chat_role_values(self):
        assert ChatRole.USER.value == "user"
        assert ChatRole.ASSISTANT.value == "assistant"

    def test_chat_type_values(self):
        assert ChatType.GENERAL.value == "general"
        assert ChatType.FINANCE.value == "finance"

    def test_valid_sets(self):
        assert "user" in VALID_ROLES
        assert "general" in VALID_CHAT_TYPES
