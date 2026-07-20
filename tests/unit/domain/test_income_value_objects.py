"""Unit tests for income value objects."""

import pytest
from app.domain.incomes.value_objects import (
    IncomeType, IncomeStatus, IncomeStability, ScheduleStatus, ProjectionMethod,
    INCOME_TYPES, INCOME_STATUSES, INCOME_STABILITY, SCHEDULE_STATUSES, PROJECTION_METHODS,
)


class TestIncomeType:
    def test_valid_types(self):
        for t in INCOME_TYPES:
            assert IncomeType(t).value == t

    def test_case_insensitive(self):
        assert IncomeType("SALARY").value == "salary"
        assert IncomeType("  Freelance  ").value == "freelance"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Tipo de ingreso no soportado"):
            IncomeType("invalid")

    def test_name_property(self):
        assert IncomeType("salary").name == "Salario"
        assert IncomeType("freelance").name == "Freelance"

    def test_str(self):
        assert str(IncomeType("salary")) == "salary"


class TestIncomeStatus:
    def test_valid_statuses(self):
        for s in INCOME_STATUSES:
            assert IncomeStatus(s).value == s

    def test_invalid_status(self):
        with pytest.raises(ValueError):
            IncomeStatus("unknown")

    def test_name_property(self):
        assert IncomeStatus("received").name == "Recibido"


class TestIncomeStability:
    def test_valid_stability(self):
        for s in INCOME_STABILITY:
            assert IncomeStability(s).value == s

    def test_invalid_stability(self):
        with pytest.raises(ValueError):
            IncomeStability("unstable")


class TestScheduleStatus:
    def test_valid_statuses(self):
        for s in SCHEDULE_STATUSES:
            assert ScheduleStatus(s).value == s

    def test_invalid(self):
        with pytest.raises(ValueError):
            ScheduleStatus("done")


class TestProjectionMethod:
    def test_valid_methods(self):
        for m in PROJECTION_METHODS:
            assert ProjectionMethod(m).value == m

    def test_invalid(self):
        with pytest.raises(ValueError):
            ProjectionMethod("random_forest")
