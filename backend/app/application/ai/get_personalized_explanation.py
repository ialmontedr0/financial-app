"""Use case: Get personalized explanation for a recommendation."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import LLMClient, LLMConfig
from app.core.config import get_settings

logger = structlog.get_logger()


class GetPersonalizedExplanationUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        recommendation: dict,
    ) -> dict:
        """Generate personalized explanation using LLM or templates."""
        from app.ai.recommendations.explainer import Explainer

        settings = get_settings()
        llm_client: LLMClient | None = None
        if settings.LLM_API_KEY:
            llm_config = LLMConfig(
                provider=settings.LLM_PROVIDER,
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            )
            llm_client = LLMClient(llm_config)

        explainer = Explainer(llm_client=llm_client)
        return await explainer.explain(self._session, user_id, recommendation)
