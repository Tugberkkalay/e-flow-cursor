"""
Expression engine: resolves {{ expr }} patterns from context.
Uses AST-based safe eval with whitelisted operations.
"""
import ast
import re
import operator
from typing import Any


ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

EXPR_PATTERN = re.compile(r"\{\{\s*(.+?)\s*\}\}")


class SafeEvalError(Exception):
    pass


def _resolve_dotted_key(key: str, context: dict) -> Any:
    """Resolve a dotted key like form.total_amount from context."""
    parts = key.strip().split(".")
    current = context
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current


def _safe_eval(node: ast.expr, context: dict) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Name):
        return _resolve_dotted_key(node.id, context)
    elif isinstance(node, ast.Attribute):
        # handle dotted access: form.total_amount
        parts = []
        n = node
        while isinstance(n, ast.Attribute):
            parts.append(n.attr)
            n = n.value
        if isinstance(n, ast.Name):
            parts.append(n.id)
        key = ".".join(reversed(parts))
        return _resolve_dotted_key(key, context)
    elif isinstance(node, ast.BinOp):
        left = _safe_eval(node.left, context)
        right = _safe_eval(node.right, context)
        op_type = type(node.op)
        if op_type not in ALLOWED_OPS:
            raise SafeEvalError(f"Operator {op_type} not allowed")
        return ALLOWED_OPS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand, context)
        op_type = type(node.op)
        if op_type not in ALLOWED_OPS:
            raise SafeEvalError(f"Operator {op_type} not allowed")
        return ALLOWED_OPS[op_type](operand)
    elif isinstance(node, ast.BoolOp):
        values = [_safe_eval(v, context) for v in node.values]
        op_type = type(node.op)
        result = values[0]
        for v in values[1:]:
            if isinstance(node.op, ast.And):
                result = result and v
            else:
                result = result or v
        return result
    elif isinstance(node, ast.Compare):
        left = _safe_eval(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            right = _safe_eval(comparator, context)
            op_type = type(op)
            if op_type not in ALLOWED_OPS:
                raise SafeEvalError(f"Operator {op_type} not allowed")
            if not ALLOWED_OPS[op_type](left, right):
                return False
            left = right
        return True
    elif isinstance(node, ast.IfExp):
        test = _safe_eval(node.test, context)
        return _safe_eval(node.body, context) if test else _safe_eval(node.orelse, context)
    elif isinstance(node, ast.List):
        return [_safe_eval(elt, context) for elt in node.elts]
    elif isinstance(node, ast.Tuple):
        return tuple(_safe_eval(elt, context) for elt in node.elts)
    elif isinstance(node, ast.Subscript):
        value = _safe_eval(node.value, context)
        if isinstance(node.slice, ast.Constant):
            return value[node.slice.value] if value else None
        return None
    elif isinstance(node, ast.Call):
        # Allow a small set of safe builtins
        func = node.func
        if isinstance(func, ast.Name) and func.id in ("len", "str", "int", "float", "bool", "abs", "round", "min", "max"):
            args = [_safe_eval(a, context) for a in node.args]
            return __builtins__[func.id](*args) if isinstance(__builtins__, dict) else getattr(__import__("builtins"), func.id)(*args)
        raise SafeEvalError(f"Function calls not allowed: {ast.dump(func)}")
    else:
        raise SafeEvalError(f"Node type not allowed: {type(node).__name__}")


class ExpressionEngine:
    @staticmethod
    def resolve(template: str, context: dict) -> Any:
        """
        Resolve {{ expr }} patterns in a string template.
        If the entire string is one expression, returns typed value.
        Otherwise returns string with expressions replaced.
        """
        if not isinstance(template, str):
            return template

        matches = list(EXPR_PATTERN.finditer(template))
        if not matches:
            return template

        # Single full-string expression → return typed
        if len(matches) == 1 and matches[0].start() == 0 and matches[0].end() == len(template):
            return ExpressionEngine._eval_expr(matches[0].group(1), context)

        # Mixed text + expressions → return string
        result = template
        for match in reversed(matches):
            value = ExpressionEngine._eval_expr(match.group(1), context)
            result = result[:match.start()] + str(value if value is not None else "") + result[match.end():]
        return result

    @staticmethod
    def _eval_expr(expr_str: str, context: dict) -> Any:
        try:
            # Try dotted key first (most common case)
            if re.match(r'^[\w.]+$', expr_str):
                val = _resolve_dotted_key(expr_str, context)
                if val is not None:
                    return val

            tree = ast.parse(expr_str, mode="eval")
            return _safe_eval(tree.body, context)
        except (SafeEvalError, SyntaxError, TypeError, KeyError, ZeroDivisionError):
            return None

    @staticmethod
    def evaluate_condition(condition: dict, context: dict) -> bool:
        """
        Evaluate a condition dict:
        { "field": "form.amount", "op": ">=", "value": 50000 }
        or compound: { "and": [...] } / { "or": [...] }
        """
        if "and" in condition:
            return all(ExpressionEngine.evaluate_condition(c, context) for c in condition["and"])
        if "or" in condition:
            return any(ExpressionEngine.evaluate_condition(c, context) for c in condition["or"])
        if "not" in condition:
            return not ExpressionEngine.evaluate_condition(condition["not"], context)

        field = condition.get("field", "")
        op = condition.get("op", "==")
        raw_value = condition.get("value")

        left = ExpressionEngine.resolve(f"{{{{{field}}}}}", context) if "{{" not in field else ExpressionEngine.resolve(field, context)
        right = ExpressionEngine.resolve(str(raw_value), context) if isinstance(raw_value, str) else raw_value

        ops = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: _to_num(a) > _to_num(b),
            ">=": lambda a, b: _to_num(a) >= _to_num(b),
            "<": lambda a, b: _to_num(a) < _to_num(b),
            "<=": lambda a, b: _to_num(a) <= _to_num(b),
            "in": lambda a, b: a in (b if isinstance(b, (list, str)) else []),
            "not_in": lambda a, b: a not in (b if isinstance(b, (list, str)) else []),
            "contains": lambda a, b: b in str(a) if a is not None else False,
            "is_empty": lambda a, _: a is None or a == "" or a == [],
            "is_not_empty": lambda a, _: a is not None and a != "" and a != [],
        }
        fn = ops.get(op, lambda a, b: False)
        try:
            return bool(fn(left, right))
        except Exception:
            return False

    @staticmethod
    def resolve_all(data: Any, context: dict) -> Any:
        """Recursively resolve expressions in any data structure."""
        if isinstance(data, str):
            return ExpressionEngine.resolve(data, context)
        if isinstance(data, dict):
            return {k: ExpressionEngine.resolve_all(v, context) for k, v in data.items()}
        if isinstance(data, list):
            return [ExpressionEngine.resolve_all(item, context) for item in data]
        return data

    @staticmethod
    def get_context_schema(context: dict, prefix: str = "") -> list[dict]:
        """Return flat list of {key, type} for autocomplete."""
        result = []
        for k, v in context.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                result.extend(ExpressionEngine.get_context_schema(v, full_key))
            else:
                result.append({"key": full_key, "type": type(v).__name__, "sample": v})
        return result


def _to_num(v):
    if v is None:
        return 0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0
