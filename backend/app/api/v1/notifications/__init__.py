from fastapi import APIRouter

from app.api.v1.notifications.router import router as notifications_router

router = APIRouter()
router.include_router(notifications_router)
