from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class NotificationMessage:
    user_id: UUID
    channel: str
    type: str
    title: str
    body: str
    data: dict[str, Any] = field(default_factory=dict)
    template_vars: dict[str, Any] | None = None


@dataclass
class NotificationResult:
    success: bool
    channel: str
    message_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseChannel(ABC):
    @abstractmethod
    async def send(self, message: NotificationMessage) -> NotificationResult:
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    def get_name(self) -> str:
        ...
