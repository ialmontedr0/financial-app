from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.api.v1.notifications import schemas as notif_schemas
from app.application.notifications.use_cases import (
    BulkDeleteNotificationsUseCase,
    BulkMarkNotificationsReadUseCase,
    DeleteNotificationUseCase,
    DeleteReadNotificationsUseCase,
    GetNotificationPreferencesUseCase,
    GetNotificationStatsUseCase,
    GetNotificationsUseCase,
    GetNotificationUseCase,
    MarkAllNotificationsReadUseCase,
    MarkNotificationReadUseCase,
    SendNotificationUseCase,
    SendTestNotificationUseCase,
    UpdateNotificationPreferencesUseCase,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "/", response_model=notif_schemas.NotificationSendResponse, status_code=status.HTTP_201_CREATED
)
async def create_notification(
    body: notif_schemas.NotificationCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = SendNotificationUseCase(db)
    results = await use_case.execute(
        user_id=user_id,
        type=body.type,
        title=body.title,
        body=body.body,
        data=body.data,
        channels=body.channels,
    )
    return notif_schemas.NotificationSendResponse(success=True, results=results)


@router.get("/", response_model=notif_schemas.NotificationListResponse)
async def list_notifications(
    channel: str | None = Query(None),
    type: str | None = Query(None, alias="type"),
    is_read: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = GetNotificationsUseCase(db)
    notifs = await use_case.execute(
        user_id=user_id,
        channel=channel,
        type_=type,
        is_read=is_read,
        skip=skip,
        limit=limit,
    )
    return notif_schemas.NotificationListResponse(notifications=notifs, total=len(notifs))


# Specific routes MUST be defined BEFORE the parameterized /{notification_id} route
# to prevent FastAPI from trying to parse "preferences", "stats", etc. as UUIDs.

@router.get("/preferences", response_model=notif_schemas.NotificationPreferenceResponse)
async def get_preferences(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = GetNotificationPreferencesUseCase(db)
    prefs = await use_case.execute(user_id)
    if not prefs:
        return notif_schemas.NotificationPreferenceResponse(
            email_enabled=True,
            push_enabled=True,
            telegram_enabled=False,
            discord_enabled=False,
            webhook_enabled=False,
        )
    return prefs


@router.put("/preferences", response_model=notif_schemas.NotificationPreferenceResponse)
async def update_preferences(
    body: notif_schemas.NotificationPreferenceUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = UpdateNotificationPreferencesUseCase(db)
    data = body.model_dump(exclude_unset=True)
    prefs = await use_case.execute(user_id, data)
    return prefs


@router.get("/stats", response_model=notif_schemas.NotificationStatsResponse)
async def get_stats(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = GetNotificationStatsUseCase(db)
    return await use_case.execute(user_id)


@router.post("/test", response_model=notif_schemas.NotificationSendResponse)
async def send_test(
    body: notif_schemas.TestNotificationRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = SendTestNotificationUseCase(db)
    email = current_user.get("email", "")
    results = await use_case.execute(user_id, email, channel=body.channel, telegram_chat_id=body.telegram_chat_id)
    return notif_schemas.NotificationSendResponse(success=True, results=results)


@router.post("/bulk-read")
async def bulk_mark_read(
    body: notif_schemas.BulkMarkReadRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = BulkMarkNotificationsReadUseCase(db)
    count = await use_case.execute(body.notification_ids, user_id)
    return {"success": True, "count": count}


@router.post("/read-all")
async def mark_all_read(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = MarkAllNotificationsReadUseCase(db)
    count = await use_case.execute(user_id)
    return {"success": True, "count": count}


@router.delete("/read", status_code=status.HTTP_200_OK)
async def delete_read_notifications(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = DeleteReadNotificationsUseCase(db)
    count = await use_case.execute(user_id)
    return {"success": True, "count": count}


@router.post("/bulk-delete")
async def bulk_delete(
    body: notif_schemas.BulkMarkReadRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = BulkDeleteNotificationsUseCase(db)
    count = await use_case.execute(body.notification_ids, user_id)
    return {"success": True, "count": count}


@router.get("/{notification_id}", response_model=notif_schemas.NotificationResponse)
async def get_notification(
    notification_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = GetNotificationUseCase(db)
    notif = await use_case.execute(notification_id, user_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = MarkNotificationReadUseCase(db)
    ok = await use_case.execute(notification_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.delete(
    "/{notification_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_notification(
    notification_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID as _UUID

    user_id = _UUID(current_user["sub"])
    use_case = DeleteNotificationUseCase(db)
    ok = await use_case.execute(notification_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
