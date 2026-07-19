"""Tests for Category domain value objects."""

import pytest

from app.domain.categories.value_objects import CategoryScope, CategoryType, PatternType


class TestCategoryType:
    def test_valid_types(self) -> None:
        for t in ["expense", "income", "transfer", "adjustment"]:
            assert str(CategoryType(t)) == t

    def test_normalized(self) -> None:
        assert str(CategoryType("EXPENSE")) == "expense"

    def test_invalid_type(self) -> None:
        with pytest.raises(ValueError, match="Tipo de categoria no soportado"):
            CategoryType("invalid")

    def test_name_property(self) -> None:
        assert CategoryType("expense").name == "Gasto"
        assert CategoryType("income").name == "Ingreso"


class TestCategoryScope:
    def test_valid_scopes(self) -> None:
        for s in ["system", "user"]:
            assert str(CategoryScope(s)) == s

    def test_invalid_scope(self) -> None:
        with pytest.raises(ValueError, match="Scope de categoria no soportado"):
            CategoryScope("admin")

    def test_name_property(self) -> None:
        assert CategoryScope("system").name == "Del Sistema"


class TestPatternType:
    def test_valid_types(self) -> None:
        for t in ["keyword", "regex", "amount_range", "merchant_exact"]:
            assert str(PatternType(t)) == t

    def test_invalid_type(self) -> None:
        with pytest.raises(ValueError, match="Tipo de patron no soportado"):
            PatternType("fuzzy")
