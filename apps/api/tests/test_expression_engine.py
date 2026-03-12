"""Tests for the expression engine."""
import pytest
from app.engine.expression import ExpressionEngine


@pytest.fixture
def engine():
    return ExpressionEngine()


@pytest.fixture
def sample_context():
    return {
        "form": {
            "total_amount": 75000,
            "currency": "TRY",
            "request_type": "Abonelik",
            "vendor_name": "ACME Corp",
            "items": [{"item_name": "Laptop", "quantity": 2, "unit_price": 37500}],
        },
        "approval": {
            "last_decision": "approved",
            "last_comment": "Budget OK",
        },
        "calc": {
            "vat_amount": 15000,
            "total_with_vat": 90000,
        },
        "flags": {
            "match_status": "matched",
            "policy_flags": [],
        },
        "system": {
            "started_by": "user-123",
            "started_at": "2026-03-12T10:00:00",
        },
    }


class TestBasicResolution:
    def test_simple_dotted_key(self, engine, sample_context):
        result = engine.resolve("{{ form.total_amount }}", sample_context)
        assert result == 75000

    def test_nested_key(self, engine, sample_context):
        result = engine.resolve("{{ approval.last_decision }}", sample_context)
        assert result == "approved"

    def test_deep_nested(self, engine, sample_context):
        result = engine.resolve("{{ system.started_by }}", sample_context)
        assert result == "user-123"

    def test_string_interpolation(self, engine, sample_context):
        result = engine.resolve("Total: {{ form.total_amount }} TRY", sample_context)
        assert result == "Total: 75000 TRY"

    def test_nonexistent_key_returns_none(self, engine, sample_context):
        result = engine.resolve("{{ form.nonexistent_field }}", sample_context)
        assert result is None

    def test_no_expression(self, engine, sample_context):
        result = engine.resolve("just a plain string", sample_context)
        assert result == "just a plain string"

    def test_non_string_passthrough(self, engine, sample_context):
        assert engine.resolve(42, sample_context) == 42
        assert engine.resolve(None, sample_context) is None


class TestArithmetic:
    def test_multiplication(self, engine, sample_context):
        result = engine.resolve("{{ form.total_amount * 1.20 }}", sample_context)
        assert result == pytest.approx(90000.0)

    def test_addition(self, engine, sample_context):
        result = engine.resolve("{{ form.total_amount + 1000 }}", sample_context)
        assert result == pytest.approx(76000.0)

    def test_division(self, engine, sample_context):
        result = engine.resolve("{{ form.total_amount / 1000 }}", sample_context)
        assert result == pytest.approx(75.0)

    def test_nested_arithmetic(self, engine, sample_context):
        result = engine.resolve("{{ form.total_amount * 0.20 }}", sample_context)
        assert result == pytest.approx(15000.0)


class TestConditions:
    def test_gte_true(self, engine, sample_context):
        result = engine.evaluate_condition(
            {"field": "form.total_amount", "op": ">=", "value": 50000},
            sample_context
        )
        assert result is True

    def test_gte_false(self, engine, sample_context):
        result = engine.evaluate_condition(
            {"field": "form.total_amount", "op": ">=", "value": 100000},
            sample_context
        )
        assert result is False

    def test_eq_string(self, engine, sample_context):
        result = engine.evaluate_condition(
            {"field": "form.request_type", "op": "==", "value": "Abonelik"},
            sample_context
        )
        assert result is True

    def test_neq_string(self, engine, sample_context):
        result = engine.evaluate_condition(
            {"field": "form.request_type", "op": "!=", "value": "Mal Alımı"},
            sample_context
        )
        assert result is True

    def test_and_condition(self, engine, sample_context):
        result = engine.evaluate_condition(
            {
                "and": [
                    {"field": "form.total_amount", "op": ">=", "value": 50000},
                    {"field": "form.request_type", "op": "==", "value": "Abonelik"},
                ]
            },
            sample_context
        )
        assert result is True

    def test_or_condition(self, engine, sample_context):
        result = engine.evaluate_condition(
            {
                "or": [
                    {"field": "form.total_amount", "op": ">=", "value": 1000000},  # False
                    {"field": "form.request_type", "op": "==", "value": "Abonelik"},  # True
                ]
            },
            sample_context
        )
        assert result is True

    def test_not_condition(self, engine, sample_context):
        result = engine.evaluate_condition(
            {"not": {"field": "form.total_amount", "op": ">=", "value": 1000000}},
            sample_context
        )
        assert result is True

    def test_in_operator(self, engine, sample_context):
        result = engine.evaluate_condition(
            {"field": "approval.last_decision", "op": "in", "value": ["approved", "revision_requested"]},
            sample_context
        )
        assert result is True

    def test_is_empty_false(self, engine, sample_context):
        result = engine.evaluate_condition(
            {"field": "form.vendor_name", "op": "is_empty", "value": None},
            sample_context
        )
        assert result is False


class TestResolveAll:
    def test_dict_resolution(self, engine, sample_context):
        data = {
            "amount": "{{ form.total_amount }}",
            "vendor": "{{ form.vendor_name }}",
            "static": "hello",
        }
        result = engine.resolve_all(data, sample_context)
        assert result["amount"] == 75000
        assert result["vendor"] == "ACME Corp"
        assert result["static"] == "hello"

    def test_list_resolution(self, engine, sample_context):
        data = ["{{ form.total_amount }}", "{{ form.currency }}", "static"]
        result = engine.resolve_all(data, sample_context)
        assert result[0] == 75000
        assert result[1] == "TRY"
        assert result[2] == "static"


class TestContextSchema:
    def test_schema_returns_keys(self, sample_context):
        schema = ExpressionEngine.get_context_schema(sample_context)
        keys = [s["key"] for s in schema]
        assert "form.total_amount" in keys
        assert "approval.last_decision" in keys
        assert "flags.match_status" in keys

    def test_schema_includes_types(self, sample_context):
        schema = ExpressionEngine.get_context_schema(sample_context)
        amount_entry = next(s for s in schema if s["key"] == "form.total_amount")
        assert amount_entry["type"] == "int"
