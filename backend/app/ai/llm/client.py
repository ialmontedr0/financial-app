"""Cliente LLM asincrono para Groq."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

import structlog
from groq import AsyncGroq

logger = structlog.get_logger()


@dataclass
class LLMConfig:
    provider: str = "groq"
    api_key: str = ""
    model: str = "llama3-70b-8192"
    max_tokens: int = 512
    temperature: float = 0.7
    timeout_seconds: int = 15


class LLMClient:
    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._client: AsyncGroq | None = None

    async def _ensure_client(self) -> AsyncGroq:
        if self._client is None:
            self._client = AsyncGroq(api_key=self._config.api_key)
        return self._client

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str | None:
        try:
            client = await self._ensure_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = await client.chat.completions.create(
                model=self._config.model,
                messages=messages,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature,
                timeout=self._config.timeout_seconds,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("llm_generation_failed", error=str(e))
            return None

    async def stream_generate(
        self, prompt: str, system_prompt: str | None = None, history: list[dict] | None = None
    ) -> AsyncIterator[str]:
        """Tokens stream desde el LLM asi como lleguen"""

        try:
            client = await self._ensure_client()
            messages: list[dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": prompt})

            stream = await client.chat.completions.create(
                model=self._config.model,
                messages=messages,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("llm_stream_failed", error=str(e))
            return
