from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LinkCodeResponse(BaseModel):
    code: str


class CheckLinkResponse(BaseModel):
    linked: bool
    telegram_chat_id: str | None = None
