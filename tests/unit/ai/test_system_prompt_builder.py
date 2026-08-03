"""Unit tests for the chat system prompt builder."""

from app.ai.chat.system_prompt import SystemPromptBuilder


class TestSystemPromptBuilder:
    def test_build_includes_base(self):
        prompt = SystemPromptBuilder().build({})
        assert "FIP" in prompt

    def test_build_includes_accounts(self):
        prompt = SystemPromptBuilder().build(
            {"accounts": [{"name": "Banco", "balance": "1000.00", "currency": "MXN"}]}
        )
        assert "Banco" in prompt
        assert "1000.00" in prompt

    def test_build_includes_today(self):
        prompt = SystemPromptBuilder().build({"today": "2026-08-03"})
        assert "2026-08-03" in prompt
