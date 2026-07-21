from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    type: str
    title: str
    body: str
    data: dict[str, Any] | None = None
    channels: list[str] | None = None


class NotificationResponse(BaseModel):
    id: UUID
    channel: str
    type: str
    title: str
    body: str
    data: dict[str, Any] | None = None
    is_read: bool
    is_sent: bool
    sent_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int


class NotificationPreferenceResponse(BaseModel):
    email_enabled: bool
    push_enabled: bool
    telegram_enabled: bool
    discord_enabled: bool
    webhook_enabled: bool
    email_types: dict[str, bool] | None = None
    push_types: dict[str, bool] | None = None
    telegram_types: dict[str, bool] | None = None
    discord_types: dict[str, bool] | None = None
    webhook_types: dict[str, bool] | None = None
    telegram_chat_id: str | None = None
    discord_webhook_url: str | None = None
    webhook_url: str | None = None

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    telegram_enabled: bool | None = None
    discord_enabled: bool | None = None
    webhook_enabled: bool | None = None
    email_types: dict[str, bool] | None = None
    push_types: dict[str, bool] | None = None
    telegram_types: dict[str, bool] | None = None
    discord_types: dict[str, bool] | None = None
    webhook_types: dict[str, bool] | None = None
    telegram_chat_id: str | None = None
    discord_webhook_url: str | None = None
    webhook_url: str | None = None
    webhook_secret: str | None = None


class NotificationStatsResponse(BaseModel):
    total: int
    unread: int
    by_channel: dict[str, int]
    by_type: dict[str, int]


class BulkMarkReadRequest(BaseModel):
    notification_ids: list[UUID]


class NotificationResultItem(BaseModel):
    success: bool
    channel: str
    error: str | None = None


class NotificationSendResponse(BaseModel):
    success: bool
    results: list[NotificationResultItem]
