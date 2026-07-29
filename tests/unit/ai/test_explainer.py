"""Tests for personalized explainer."""

from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.recommendations.explainer import (
    Explainer,
    _EXPLANATION_CACHE,
    _CACHE_TTL_SECONDS,
)


class TestExplainer:
    def test_fallback_explanation(self):
        explainer = Explainer()
        rec = {
            "type": "unknown_type",
            "title": "Test Rec",
            "description": "Test description",
            "priority": "medium",
            "estimated_savings": 1000,
            "confidence": 0.7,
        }
        result = explainer._fallback_explanation(rec)
        assert result["headline"] == "Test Rec"
        assert result["personalized"] is False
        assert result["llm_generated"] is False

    def test_fill_template_simple(self):
        explainer = Explainer()
        template = "Gastaste {amount:.0f} este mes."
        features = {"amount": 5000}
        result = explainer._fill_template(template, features)
        assert result == "Gastaste 5000 este mes."

    def test_fill_template_with_computed(self):
        explainer = Explainer()
        template = "Ahorro anual: {annual:.0f}"
        features = {"savings": 1000}
        result = explainer._fill_template(template, features)
        assert result == "Ahorro anual: 12000"

    def test_fill_template_missing_key_returns_raw(self):
        explainer = Explainer()
        template = "Gastaste {missing:.0f} este mes."
        features = {"amount": 5000}
        result = explainer._fill_template(template, features)
        assert result == template  # Returns unformatted on KeyError

    def test_determine_tone_urgent(self):
        explainer = Explainer()
        rec = {"priority": "high", "confidence": 0.9}
        assert explainer._determine_tone(rec, {}) == "urgent"

    def test_determine_tone_concerned(self):
        explainer = Explainer()
        rec = {"priority": "high", "confidence": 0.5}
        assert explainer._determine_tone(rec, {}) == "concerned"

    def test_determine_tone_informative(self):
        explainer = Explainer()
        rec = {"priority": "low", "confidence": 0.3}
        assert explainer._determine_tone(rec, {}) == "informative"

    def test_determine_tone_encouraging(self):
        explainer = Explainer()
        rec = {"priority": "medium", "confidence": 0.5}
        assert explainer._determine_tone(rec, {}) == "encouraging"

    def test_parse_llm_json_valid(self):
        explainer = Explainer()
        raw = json.dumps({
            "headline": "Reduce gastos",
            "why": "Porque gastas mucho",
            "how": "Detectado en tus transacciones",
            "impact": "Ahorrarias 1000/mes",
            "action": "Revisa tus suscripciones",
        })
        result = explainer._parse_llm_json(raw)
        assert result is not None
        assert result["headline"] == "Reduce gastos"

    def test_parse_llm_json_with_code_fence(self):
        explainer = Explainer()
        raw = """```json
{"headline": "Test", "why": "w", "how": "h", "impact": "i", "action": "a"}
```"""
        result = explainer._parse_llm_json(raw)
        assert result is not None
        assert result["headline"] == "Test"

    def test_parse_llm_json_missing_keys(self):
        explainer = Explainer()
        raw = json.dumps({"headline": "Test"})
        result = explainer._parse_llm_json(raw)
        assert result is None

    def test_parse_llm_json_invalid(self):
        explainer = Explainer()
        raw = "not json at all"
        result = explainer._parse_llm_json(raw)
        assert result is None

    def test_cache_key_is_deterministic(self):
        explainer = Explainer()
        uid = "550e8400-e29b-41d4-a716-446655440000"
        key1 = explainer._cache_key(uid, "reduce_spending", {"amount": 5000})
        key2 = explainer._cache_key(uid, "reduce_spending", {"amount": 5000})
        assert key1 == key2

    def test_cache_key_differs_by_type(self):
        explainer = Explainer()
        uid = "550e8400-e29b-41d4-a716-446655440000"
        key1 = explainer._cache_key(uid, "reduce_spending", {})
        key2 = explainer._cache_key(uid, "increase_savings", {})
        assert key1 != key2

    def test_cache_key_differs_by_features(self):
        explainer = Explainer()
        uid = "550e8400-e29b-41d4-a716-446655440000"
        key1 = explainer._cache_key(uid, "reduce_spending", {"amount": 1000})
        key2 = explainer._cache_key(uid, "reduce_spending", {"amount": 2000})
        assert key1 != key2


class TestExplainerWithLLM:
    @patch("app.ai.recommendations.explainer._EXPLANATION_CACHE", {})
    async def test_llm_path_success(self):
        llm_client = AsyncMock()
        llm_client.generate = AsyncMock(
            return_value=json.dumps({
                "headline": "LLM Headline",
                "why": "LLM Why",
                "how": "LLM How",
                "impact": "LLM Impact",
                "action": "LLM Action",
            })
        )

        explainer = Explainer(llm_client=llm_client)
        explainer._get_context_data = AsyncMock(return_value={
            "income": 50000, "expense": 30000, "balance": 20000,
            "top_category": "Comida", "tx_count": 30, "months_data": 6,
        })

        rec = {
            "type": "reduce_spending",
            "title": "Test",
            "priority": "high",
            "estimated_savings": 5000,
            "confidence": 0.8,
            "features_used": {"amount": 10000},
        }

        mock_session = AsyncMock()
        result = await explainer.explain(mock_session, "user-1", rec)

        assert result["headline"] == "LLM Headline"
        assert result["llm_generated"] is True
        assert result["personalized"] is True
        assert result["rec_type"] == "reduce_spending"

    @patch("app.ai.recommendations.explainer._EXPLANATION_CACHE", {})
    async def test_llm_failure_falls_back_to_template(self):
        llm_client = AsyncMock()
        llm_client.generate = AsyncMock(return_value=None)

        explainer = Explainer(llm_client=llm_client)

        rec = {
            "type": "reduce_spending",
            "title": "Test",
            "priority": "medium",
            "features_used": {"amount": 5000, "pct": 20, "avg": 3000, "category": "Comida", "cat_share": 40, "savings": 1000},
        }

        mock_session = AsyncMock()
        with patch.object(explainer, "_get_context_data", AsyncMock(return_value={})):
            with patch.object(explainer, "_get_user_preferences", AsyncMock(return_value={"language": "es", "currency": "DOP"})):
                result = await explainer.explain(mock_session, "user-1", rec)

        assert result["llm_generated"] is False
        assert result["headline"] == "Tu gasto ha aumentado significativamente."
        assert result["personalized"] is True

    @patch("app.ai.recommendations.explainer._EXPLANATION_CACHE", {})
    async def test_no_llm_client_uses_templates(self):
        explainer = Explainer(llm_client=None)

        rec = {
            "type": "reduce_spending",
            "title": "Test",
            "features_used": {"amount": 5000, "pct": 20, "avg": 3000, "category": "Comida", "cat_share": 40, "savings": 1000},
        }

        mock_session = AsyncMock()
        with patch.object(explainer, "_get_user_preferences", AsyncMock(return_value={"language": "es", "currency": "DOP"})):
            result = await explainer.explain(mock_session, "user-1", rec)

        assert result["llm_generated"] is False
        assert "Tu gasto" in result["headline"]

    @patch("app.ai.recommendations.explainer._EXPLANATION_CACHE", {})
    async def test_llm_json_parse_failure_falls_back(self):
        llm_client = AsyncMock()
        llm_client.generate = AsyncMock(return_value="not valid json at all")

        explainer = Explainer(llm_client=llm_client)

        rec = {
            "type": "reduce_spending",
            "title": "Test",
            "priority": "medium",
            "features_used": {"amount": 5000, "pct": 20, "avg": 3000, "category": "Comida", "cat_share": 40, "savings": 1000},
        }

        mock_session = AsyncMock()
        with patch.object(explainer, "_get_context_data", AsyncMock(return_value={})):
            with patch.object(explainer, "_get_user_preferences", AsyncMock(return_value={"language": "es", "currency": "DOP"})):
                result = await explainer.explain(mock_session, "user-1", rec)

        assert result["llm_generated"] is False
        assert "Tu gasto" in result["headline"]


class TestExplainerCache:
    def setup_method(self):
        _EXPLANATION_CACHE.clear()

    @patch("app.ai.recommendations.explainer._EXPLANATION_CACHE", {})
    async def test_cache_hit_returns_cached(self):
        llm_client = AsyncMock()
        cached_value = {"headline": "CACHED", "llm_generated": True}
        cache_key = "test-key"

        explainer = Explainer(llm_client=llm_client)
        # Manually inject into cache with a fresh timestamp
        from app.ai.recommendations.explainer import _EXPLANATION_CACHE
        _EXPLANATION_CACHE[cache_key] = (time.time(), cached_value)

        # Override _cache_key to return our test key
        explainer._cache_key = lambda uid, rt, feats: cache_key  # type: ignore

        rec = {"type": "test", "features_used": {}}
        mock_session = AsyncMock()

        result = await explainer._try_llm_explanation(mock_session, "user-1", rec)

        assert result is not None
        assert result["headline"] == "CACHED"
        # LLM should NOT have been called
        llm_client.generate.assert_not_called()
