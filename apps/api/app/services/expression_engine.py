from __future__ import annotations

import ast
import re
from typing import Any

EXPR_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}")

SAFE_FUNCTIONS = {
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
}

ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Subscript,
    ast.Attribute,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.IfExp,
)


def _get_attr(value: Any, attr: str) -> Any:
    if isinstance(value, dict):
        return value.get(attr)
    return getattr(value, attr, None)


def _eval(node: ast.AST, context: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval(node.body, context)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        return context.get(node.id)
    if isinstance(node, ast.Attribute):
        return _get_attr(_eval(node.value, context), node.attr)
    if isinstance(node, ast.Subscript):
        value = _eval(node.value, context)
        key = _eval(node.slice, context)
        return value[key]
    if isinstance(node, ast.List):
        return [_eval(elt, context) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval(elt, context) for elt in node.elts)
    if isinstance(node, ast.Dict):
        return {_eval(k, context): _eval(v, context) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand, context)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, context)
        right = _eval(node.right, context)
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
        if isinstance(node.op, ast.Pow):
            return left**right
    if isinstance(node, ast.BoolOp):
        values = [_eval(v, context) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    if isinstance(node, ast.Compare):
        left = _eval(node.left, context)
        for op, comp_node in zip(node.ops, node.comparators):
            right = _eval(comp_node, context)
            ok = False
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            elif isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            elif isinstance(op, ast.In):
                ok = left in right
            elif isinstance(op, ast.NotIn):
                ok = left not in right
            if not ok:
                return False
            left = right
        return True
    if isinstance(node, ast.Call):
        func = _eval(node.func, context)
        args = [_eval(arg, context) for arg in node.args]
        kwargs = {kw.arg: _eval(kw.value, context) for kw in node.keywords}
        if func in SAFE_FUNCTIONS.values():
            return func(*args, **kwargs)
        raise ValueError("Function not allowed")
    if isinstance(node, ast.IfExp):
        return _eval(node.body if _eval(node.test, context) else node.orelse, context)
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


def safe_eval(expr: str, context: dict[str, Any]) -> Any:
    parsed = ast.parse(expr, mode="eval")
    for node in ast.walk(parsed):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ValueError(f"Unsafe token {type(node).__name__}")
    return _eval(parsed, context)


def resolve_expression(template: str, context: dict[str, Any]) -> Any:
    stripped = template.strip()
    whole = EXPR_PATTERN.fullmatch(stripped)
    if whole:
        return safe_eval(whole.group(1), context)

    def repl(match: re.Match[str]) -> str:
        return str(safe_eval(match.group(1), context))

    return EXPR_PATTERN.sub(repl, template)
