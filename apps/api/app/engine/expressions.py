"""Expression engine for {{ }} template resolution with safe evaluation."""
import ast
import re
import operator
from typing import Any


SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
}

SAFE_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "sum": sum,
}


def _resolve_dotted(name: str, context: dict) -> Any:
    parts = name.split(".")
    current = context
    for part in parts:
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                return None
        else:
            return None
    return current


class SafeEvaluator(ast.NodeVisitor):
    def __init__(self, context: dict):
        self.context = context

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        return node.value

    def visit_Num(self, node):
        return node.n

    def visit_Str(self, node):
        return node.s

    def visit_NameConstant(self, node):
        return node.value

    def visit_Name(self, node):
        name = node.id
        if name in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[name]
        if name in ("True", "true"):
            return True
        if name in ("False", "false"):
            return False
        if name in ("None", "null"):
            return None
        return _resolve_dotted(name, self.context)

    def visit_Attribute(self, node):
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        parts.reverse()
        dotted = ".".join(parts)
        return _resolve_dotted(dotted, self.context)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        if left is None:
            left = 0
        if right is None:
            right = 0
        return op_func(left, right)

    def visit_BoolOp(self, node):
        op_type = type(node.op)
        if op_type == ast.And:
            result = True
            for v in node.values:
                result = result and self.visit(v)
            return result
        elif op_type == ast.Or:
            result = False
            for v in node.values:
                result = result or self.visit(v)
            return result
        raise ValueError(f"Unsupported bool op: {op_type.__name__}")

    def visit_Compare(self, node):
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            op_func = SAFE_OPERATORS.get(type(op))
            if op_func is None:
                if isinstance(op, ast.In):
                    if right is None:
                        return False
                    return left in right
                elif isinstance(op, ast.NotIn):
                    if right is None:
                        return True
                    return left not in right
                raise ValueError(f"Unsupported comparison: {type(op).__name__}")
            if left is None and right is not None:
                return False
            if not op_func(left, right):
                return False
            left = right
        return True

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Unsupported unary: {type(node.op).__name__}")

    def visit_Call(self, node):
        func = self.visit(node.func)
        if not callable(func):
            raise ValueError(f"Not callable: {func}")
        if func not in SAFE_FUNCTIONS.values():
            raise ValueError(f"Function not allowed")
        args = [self.visit(arg) for arg in node.args]
        return func(*args)

    def visit_IfExp(self, node):
        if self.visit(node.test):
            return self.visit(node.body)
        return self.visit(node.orelse)

    def visit_Subscript(self, node):
        value = self.visit(node.value)
        if isinstance(node.slice, ast.Constant):
            idx = node.slice.value
        elif isinstance(node.slice, ast.Index):
            idx = self.visit(node.slice.value)
        else:
            idx = self.visit(node.slice)
        if value is None:
            return None
        return value[idx]

    def visit_List(self, node):
        return [self.visit(e) for e in node.elts]

    def visit_Tuple(self, node):
        return tuple(self.visit(e) for e in node.elts)

    def visit_Dict(self, node):
        return {self.visit(k): self.visit(v) for k, v in zip(node.keys, node.values)}

    def generic_visit(self, node):
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def safe_eval(expression: str, context: dict) -> Any:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        evaluator = SafeEvaluator(context)
        return evaluator.visit(tree)
    except Exception as e:
        raise ValueError(f"Expression error: {e}")


TEMPLATE_PATTERN = re.compile(r"\{\{\s*(.+?)\s*\}\}")


def resolve(template: str, context: dict) -> Any:
    """Resolve a template string with {{ expr }} patterns."""
    if not isinstance(template, str):
        return template

    full_match = re.fullmatch(r"\{\{\s*(.+?)\s*\}\}", template.strip())
    if full_match:
        return safe_eval(full_match.group(1), context)

    def replacer(match):
        expr = match.group(1)
        try:
            result = safe_eval(expr, context)
            return str(result) if result is not None else ""
        except Exception:
            return match.group(0)

    return TEMPLATE_PATTERN.sub(replacer, template)


def resolve_deep(obj: Any, context: dict) -> Any:
    """Recursively resolve all {{ }} in dicts/lists/strings."""
    if isinstance(obj, str):
        return resolve(obj, context)
    elif isinstance(obj, dict):
        return {k: resolve_deep(v, context) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_deep(item, context) for item in obj]
    return obj


def get_context_keys(context: dict, prefix: str = "") -> list[str]:
    """Get all available keys from context for autocomplete."""
    keys = []
    for k, v in context.items():
        full_key = f"{prefix}.{k}" if prefix else k
        keys.append(full_key)
        if isinstance(v, dict):
            keys.extend(get_context_keys(v, full_key))
    return keys
