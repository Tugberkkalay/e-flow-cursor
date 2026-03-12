"""Tests for the expression engine."""
from app.engine.expressions import resolve, safe_eval, resolve_deep, get_context_keys


def test_simple_resolve():
    ctx = {"form": {"total_amount": 50000}}
    assert resolve("{{ form.total_amount }}", ctx) == 50000


def test_arithmetic():
    ctx = {"form": {"quantity": 10, "unit_price": 3500, "vat_rate": 20}}
    result = resolve("{{ form.quantity * form.unit_price * (1 + form.vat_rate / 100) }}", ctx)
    assert result == 42000.0


def test_comparison():
    ctx = {"form": {"total_amount": 60000}}
    assert resolve("{{ form.total_amount >= 50000 }}", ctx) is True


def test_comparison_false():
    ctx = {"form": {"total_amount": 30000}}
    assert resolve("{{ form.total_amount >= 50000 }}", ctx) is False


def test_string_equality():
    ctx = {"form": {"request_type": "subscription"}}
    assert resolve("{{ form.request_type == 'subscription' }}", ctx) is True


def test_boolean_or():
    ctx = {"form": {"total_amount": 30000, "request_type": "subscription"}}
    result = resolve("{{ form.total_amount >= 50000 or form.request_type == 'subscription' }}", ctx)
    assert result is True


def test_boolean_and():
    ctx = {"form": {"total_amount": 60000, "request_type": "goods"}}
    result = resolve("{{ form.total_amount >= 50000 and form.request_type == 'goods' }}", ctx)
    assert result is True


def test_none_handling():
    ctx = {"form": {}}
    result = resolve("{{ form.total_amount }}", ctx)
    assert result is None


def test_template_string_interpolation():
    ctx = {"system": {"year": "2024", "seq": "AB12CD"}}
    result = resolve("PO-{{ system.year }}-{{ system.seq }}", ctx)
    assert result == "PO-2024-AB12CD"


def test_resolve_deep():
    ctx = {"form": {"total": 100}, "system": {"year": "2024"}}
    obj = {"po_no": "PO-{{ system.year }}", "amount": "{{ form.total }}"}
    result = resolve_deep(obj, ctx)
    assert result["po_no"] == "PO-2024"
    assert result["amount"] == 100


def test_safe_eval_functions():
    assert safe_eval("abs(-5)", {}) == 5
    assert safe_eval("max(1, 2, 3)", {}) == 3
    assert safe_eval("round(3.7)", {}) == 4


def test_context_keys():
    ctx = {"form": {"title": "t", "amount": 0}, "system": {"id": "x"}}
    keys = get_context_keys(ctx)
    assert "form" in keys
    assert "form.title" in keys
    assert "form.amount" in keys
    assert "system.id" in keys


def test_nested_access():
    ctx = {"extract": {"dates": {"start": "2024-01-01", "end": "2024-12-31"}}}
    assert resolve("{{ extract.dates.start }}", ctx) == "2024-01-01"
