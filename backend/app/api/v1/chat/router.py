"""Chat endpoints with SSE streaming."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.api.v1.chat.schemas import CreateSessionRequest, SendMessageRequest

router = APIRouter(prefix="/chat", tags=["Chat"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/sessions", status_code=201)
async def create_session(
    body: CreateSessionRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.chat.create_session import CreateChatSessionUseCase

    return await CreateChatSessionUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        title=body.title,
        chat_type=body.chat_type,
    )


@router.get("/sessions")
async def list_sessions(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.chat.list_sessions import ListChatSessionsUseCase

    return await ListChatSessionsUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.chat.get_session import GetChatSessionUseCase

    return await GetChatSessionUseCase(db).execute(uuid.UUID(current_user["sub"]), session_id)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.chat.delete_session import DeleteChatSessionUseCase

    return await DeleteChatSessionUseCase(db).execute(uuid.UUID(current_user["sub"]), session_id)


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    from app.application.chat.send_message import SendMessageUseCase

    user_id = uuid.UUID(current_user["sub"])

    async def event_stream():
        async for event in SendMessageUseCase(db).execute(
            user_id, session_id, content=body.content
        ):
            event_name = event["type"]
            payload = {"content": event["content"]}
            yield _sse(event_name, payload)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
