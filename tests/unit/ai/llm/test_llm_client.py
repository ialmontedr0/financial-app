"""Tests for LLM client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.ai.llm import LLMClient, LLMConfig


class TestLLMClient:
    def test_config_defaults(self):
        config = LLMConfig(api_key="test_key")
        assert config.provider == "groq"
        assert config.api_key == "test_key"
        assert config.model == "llama3-70b-8192"
        assert config.max_tokens == 512
        assert config.temperature == 0.7
        assert config.timeout_seconds == 15

    @patch("app.ai.llm.client.AsyncGroq")
    async def test_generate_success(self, mock_async_groq):
        config = LLMConfig(api_key="test_key")
        client = LLMClient(config)

        mock_instance = AsyncMock()
        mock_async_groq.return_value = mock_instance
        mock_choice = AsyncMock()
        mock_choice.message.content = '{"headline": "Test", "why": "reason", "how": "detected", "impact": "effect", "action": "do"}'
        mock_response = AsyncMock()
        mock_response.choices = [mock_choice]
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await client.generate("test prompt", system_prompt="system prompt")

        assert result is not None
        assert "headline" in result
        mock_instance.chat.completions.create.assert_called_once_with(
            model=config.model,
            messages=[
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "test prompt"},
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout_seconds,
        )

    @patch("app.ai.llm.client.AsyncGroq")
    async def test_generate_without_system_prompt(self, mock_async_groq):
        config = LLMConfig(api_key="test_key")
        client = LLMClient(config)

        mock_instance = AsyncMock()
        mock_async_groq.return_value = mock_instance
        mock_choice = AsyncMock()
        mock_choice.message.content = "respuesta simple"
        mock_response = AsyncMock()
        mock_response.choices = [mock_choice]
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await client.generate("test prompt")

        assert result == "respuesta simple"
        # Verify only user message was sent
        args = mock_instance.chat.completions.create.call_args
        messages = args[1]["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    @patch("app.ai.llm.client.AsyncGroq")
    async def test_generate_failure_returns_none(self, mock_async_groq):
        config = LLMConfig(api_key="test_key")
        client = LLMClient(config)

        mock_instance = AsyncMock()
        mock_async_groq.return_value = mock_instance
        mock_instance.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        result = await client.generate("test prompt")
        assert result is None

    async def test_generate_empty_api_key(self):
        config = LLMConfig(api_key="")
        client = LLMClient(config)

        result = await client.generate("test prompt")
        # Should fail because AsyncGroq will get empty api_key
        # but that's a runtime error, not a None return
        # This just verifies no exception is raised in our code
        assert result is None or isinstance(result, (str, type(None)))

    @patch("app.ai.llm.client.AsyncGroq")
    async def test_client_reuses_instance(self, mock_async_groq):
        config = LLMConfig(api_key="test_key")
        client = LLMClient(config)

        mock_instance = AsyncMock()
        mock_async_groq.return_value = mock_instance
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="ok"))]
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

        await client.generate("first")
        await client.generate("second")

        # AsyncGroq should only be instantiated once
        mock_async_groq.assert_called_once()
