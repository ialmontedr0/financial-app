"""Use case: persist a user message and stream the assistant reply.

Returns an async iterator of SSE chunks. Falls back to a deterministic
message when the LLM is not configured or fails.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import structlog

from app.ai.chat.system_prompt import SystemPromptBuilder
from app.ai.llm.client import LLMClient, LLMConfig
from app.application.chat.financial_context import build_financial_context
from app.domain.chat.value_objects import MAX_MESSAGE_LENGTH
from app.infrastructure.repositories.chat_repository import ChatRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date  # noqa: F401

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class SendMessageUseCase:
    def __init__(self, session: AsyncSession, llm_client: LLMClient | None = None) -> None:
        self._session = session
        self._repo = ChatRepository(session)
        self._llm = llm_client

    def _ensure_llm(self) -> LLMClient:
        if self._llm is not None:
            return self._llm
        from app.core.config import get_settings

        settings = get_settings()
        return LLMClient(
            LLMConfig(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            )
        )

    async def _history_messages(self, session_id: uuid.UUID) -> list[dict]:
        history = await self._repo.list_messages(session_id)
        # Solo manda el contexto reciente (últimas 12) para no agotar el contexto.
        return [{"role": m.role, "content": m.content} for m in history[-12:]]

    async def _build_system_prompt(self, user_id: uuid.UUID) -> str:
        from datetime import date as date_type

        today = date_type.today()  # noqa: DTZ011
        context = await build_financial_context(self._session, user_id, today)
        return SystemPromptBuilder().build(context)

    async def execute(
        self, user_id: uuid.UUID, session_id: uuid.UUID, *, content: str
    ) -> AsyncIterator[dict]:
        from app.middleware.error_handler import NotFoundError, ValidationError

        session = await self._repo.get_session(session_id, user_id)
        if session is None:
            raise NotFoundError("ChatSession")

        clean = content.strip()
        if not clean:
            raise ValidationError("El mensaje no puede estar vacio")
        clean = clean[:MAX_MESSAGE_LENGTH]

        await self._repo.add_message(session_id, role="user", content=clean)

        llm = self._ensure_llm()
        system_prompt = await self._build_system_prompt(user_id)
        history = await self._history_messages(session_id)
        history = history[:-1]  # el último "user" ya está incluido como pregunta actual

        full_reply: list[str] = []
        try:
            async for chunk in llm.stream_generate(
                prompt=clean,
                system_prompt=system_prompt,
                history=history,
            ):
                if chunk:
                    full_reply.append(chunk)
                    yield {"type": "delta", "content": chunk}
        except Exception as e:
            logger.error("chat_llm_error", user_id=str(user_id), error=str(e))

        reply = "".join(full_reply).strip()
        if not reply:
            reply = (
                "Lo siento, el asistente no está disponible ahora mismo. "
                "Revisa tu API key de Groq en la configuración del backend (LLM_API_KEY)."
            )
            yield {"type": "delta", "content": reply}

        await self._repo.add_message(session_id, role="assistant", content=reply)
        await self._repo.touch_session(session_id)

        if session.title == "Nueva conversación":
            session.title = clean[:50]
            await self._session.flush()

        yield {"type": "done", "content": reply}
