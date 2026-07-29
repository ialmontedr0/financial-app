from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.api.v1.telegram import schemas as tg_schemas
from app.application.telegram.use_cases import GenerateLinkCodeUseCase, ProcessTelegramUpdateUseCase, UnlinkTelegramUseCase
from app.core.config import get_settings
from app.infrastructure.repositories.notification_repository import NotificationRepository

router = APIRouter(prefix="/telegram", tags=["Telegram"])
settings = get_settings()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    expected = settings.TELEGRAM_WEBHOOK_SECRET
    if expected and secret != expected:
        raise HTTPException(status_code=403, detail="Invalid secret token")
    body = await request.json()
    use_case = ProcessTelegramUpdateUseCase(db)
    await use_case.execute(body)
    return {"ok": True}


@router.post("/link-code", response_model=tg_schemas.LinkCodeResponse)
async def generate_link_code(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(current_user["sub"])
    use_case = GenerateLinkCodeUseCase(db)
    code = await use_case.execute(user_id)
    return tg_schemas.LinkCodeResponse(code=code)


@router.get("/check-link", response_model=tg_schemas.CheckLinkResponse)
async def check_link(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(current_user["sub"])
    repo = NotificationRepository(db)
    prefs = await repo.get_user_preferences(user_id)
    if prefs and prefs.telegram_chat_id:
        return tg_schemas.CheckLinkResponse(linked=True, telegram_chat_id=prefs.telegram_chat_id)
    return tg_schemas.CheckLinkResponse(linked=False)


@router.post("/unlink")
async def unlink_telegram(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(current_user["sub"])
    use_case = UnlinkTelegramUseCase(db)
    await use_case.execute(user_id)
    return {"success": True}
