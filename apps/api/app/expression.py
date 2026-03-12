from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from typing import Any

EXPR_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}")


class ExpressionError(ValueError):
    pass


ALLOWED_FUNCTIONS = {
    "abs": abs,
    "len": len,
    "max": max,
    "min": min,
    "round": round,
    "sum": sum,
}


def _resolve_attribute(value: Any, attr: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(attr)
    return getattr(value, attr, None)


def _eval_node(node: ast.AST, context: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, context)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in ALLOWED_FUNCTIONS:
            return ALLOWED_FUNCTIONS[node.id]
        if node.id in context:
            return context[node.id]
        raise ExpressionError(f"Unknown name '{node.id}'")
    if isinstance(node, ast.Attribute):
        base = _eval_node(node.value, context)
        return _resolve_attribute(base, node.attr)
    if isinstance(node, ast.Subscript):
        base = _eval_node(node.value, context)
        key = _eval_node(node.slice, context)
        return base[key]
    if isinstance(node, ast.List):
        return [_eval_node(elt, context) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(elt, context) for elt in node.elts)
    if isinstance(node, ast.Dict):
        return {_eval_node(k, context): _eval_node(v, context) for k, v in zip(node.keys, node.values, strict=False)}
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, context)
        right = _eval_node(node.right, context)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        raise ExpressionError("Unsupported binary operator")
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, context)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.Not):
            return not operand
        raise ExpressionError("Unsupported unary operator")
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(value, context) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise ExpressionError("Unsupported boolean operator")
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, context)
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            right = _eval_node(comparator, context)
            result = False
            if isinstance(op, ast.Eq):
                result = left == right
            elif isinstance(op, ast.NotEq):
                result = left != right
            elif isinstance(op, ast.Gt):
                result = left > right
            elif isinstance(op, ast.GtE):
                result = left >= right
            elif isinstance(op, ast.Lt):
                result = left < right
            elif isinstance(op, ast.LtE):
                result = left <= right
            elif isinstance(op, ast.In):
                result = left in right
            elif isinstance(op, ast.NotIn):
                result = left not in right
            else:
                raise ExpressionError("Unsupported comparison operator")
            if not result:
                return False
            left = right
        return True
    if isinstance(node, ast.Call):
        func = _eval_node(node.func, context)
        if func not in ALLOWED_FUNCTIONS.values():
            raise ExpressionError("Function not allowed")
        args = [_eval_node(arg, context) for arg in node.args]
        kwargs = {kw.arg: _eval_node(kw.value, context) for kw in node.keywords}
        return func(*args, **kwargs)
    raise ExpressionError(f"Unsupported expression node '{type(node).__name__}'")


def evaluate_expression(expression: str, context: dict[str, Any]) -> Any:
    parsed = ast.parse(expression, mode="eval")
    return _eval_node(parsed, context)


def resolve_template(value: Any, context: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    full_match = EXPR_PATTERN.fullmatch(stripped)
    if full_match:
        return evaluate_expression(full_match.group(1), context)

    def replacer(match: re.Match[str]) -> str:
        result = evaluate_expression(match.group(1), context)
        return "" if result is None else str(result)

    if EXPR_PATTERN.search(value):
        return EXPR_PATTERN.sub(replacer, value)
    return value


def context_schema_from_sample(sample: dict[str, Any]) -> dict[str, Any]:
    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: walk(inner) for key, inner in value.items()}
        if isinstance(value, list):
            first = value[0] if value else "any"
            return [walk(first)]
        return type(value).__name__

    return walk(sample)
