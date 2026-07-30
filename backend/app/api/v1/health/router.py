"""Health check endpoints with full dependency verification."""

from __future__ import annotations

import shutil
import time
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends
from redis import asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get("/health", response_model=None)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Full health check — app, database, redis, disk, memory."""
    status = "healthy"
    checks = {}
    all_healthy = True

    try:
        result = await db.execute(text("SELECT 1 AS ok"))
        row = result.one()
        checks["database"] = {"status": "ok" if row.ok == 1 else "error"}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}
        all_healthy = False

    try:
        redis = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        pong = await redis.ping()
        checks["redis"] = {"status": "ok" if pong else "error"}
        await redis.aclose()
    except Exception as e:
        checks["redis"] = {"status": "error", "error": str(e)}
        all_healthy = False

    try:
        usage = shutil.disk_usage("/")
        free_gb = usage.free / (1024**3)
        checks["disk"] = {"free_gb": round(free_gb, 2), "status": "ok" if free_gb > 1.0 else "warning"}
        if free_gb < 1.0:
            all_healthy = False
    except Exception as e:
        checks["disk"] = {"status": "error", "error": str(e)}

    try:
        import psutil

        mem = psutil.virtual_memory()
        checks["memory"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent,
            "status": "ok" if mem.percent < 90 else "warning",
        }
        if mem.percent >= 90:
            all_healthy = False
    except ImportError:
        pass
    except Exception as e:
        checks["memory"] = {"status": "error", "error": str(e)}

    if not all_healthy:
        status = "degraded"

    return {
        "status": status,
        "version": settings.APP_VERSION,
        "uptime_seconds": int(time.time() - _start_time),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@router.get("/health/readiness")
async def readiness():
    """Simple readiness probe — app is ready to serve traffic."""
    return {"status": "ready"}


@router.get("/health/liveness")
async def liveness():
    """Simple liveness probe — app process is alive."""
    return {"status": "alive"}
