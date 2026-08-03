"""Domain value objects for the AI chat module."""

from __future__ import annotations

import enum


class ChatRole(str, enum.Enum):  # noqa: UP042
    USER = "user"
    ASSISTANT = "assistant"


class ChatType(str, enum.Enum):  # noqa: UP042
    GENERAL = "general"
    FINANCE = "finance"


VALID_CHAT_TYPES = {t.value for t in ChatType}
VALID_ROLES = {r.value for r in ChatRole}
MAX_TITLE_LENGTH = 200
MAX_MESSAGE_LENGTH = 4000
