"""Language values, strict type rules, formatting, and resource guards."""
from __future__ import annotations
from dataclasses import dataclass
import math
from .errors import fail


@dataclass(frozen=True)
class Limits:
    max_steps: int = 200_000
    timeout_seconds: float = 3.0
    max_call_depth: int = 100
    max_items: int = 10_000
    max_string: int = 100_000
    max_output: int = 200_000
    max_integer_bits: int = 4_096
    max_value_depth: int = 50
    max_value_nodes: int = 50_000


def kind(value: object) -> str:
    return {type(None): "void", bool: "boolean", int: "integer", float: "decimal",
            str: "text", list: "list", dict: "map"}.get(type(value), "internal")


def number(value):
    if type(value) not in (int, float):
        fail("TypeError", f"Expected a number, received {kind(value)}.", code="Q3004")
    return value


def integer(value):
    if type(value) is not int:
        fail("TypeError", f"Expected an integer, received {kind(value)}.", code="Q3004")
    return value


def text(value):
    if type(value) is not str:
        fail("TypeError", f"Expected text, received {kind(value)}.", code="Q3004")
    return value


def array(value):
    if type(value) is not list:
        fail("TypeError", f"Expected a list, received {kind(value)}.", code="Q3004")
    return value


def mapping(value):
    if type(value) is not dict:
        fail("TypeError", f"Expected a map, received {kind(value)}.", code="Q3004")
    return value


def sequence(value):
    if type(value) not in (str, list):
        fail("TypeError", f"Expected text or a list, received {kind(value)}.", code="Q3004")
    return value


def collection(value):
    if type(value) not in (str, list, dict):
        fail("TypeError", f"Expected text, a list, or a map; received {kind(value)}.", code="Q3004")
    return value


def boolean(value):
    if type(value) is not bool:
        fail("TypeError", f"Expected aye or nay, received {kind(value)}.", code="Q3004")
    return value


def equal(left, right, seen=None) -> bool:
    """Numbers compare across integer/decimal types, but booleans are not numbers."""
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if type(left) is not type(right):
        return False
    if type(left) not in (list, dict):
        return left == right
    if len(left) != len(right):
        return False
    if seen is None:
        seen = set()
    pair = (id(left), id(right))
    if pair in seen:
        return True
    seen.add(pair)
    if type(left) is list:
        return all(equal(a, b, seen) for a, b in zip(left, right))
    return left.keys() == right.keys() and all(equal(left[k], right[k], seen) for k in left)


def ordered(left, right, operator: str) -> bool:
    if not ((type(left) in (int, float) and type(right) in (int, float))
            or (type(left) is str and type(right) is str)):
        fail("TypeError", "Ordering needs two numbers or two text values.", code="Q3004")
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    return left >= right


def check_length(length: int, maximum: int, label: str) -> None:
    if length > maximum:
        fail("LimitError", f"{label} exceeds the limit of {maximum:,}.", code="Q4006")


def guard(value, limits: Limits) -> None:
    """Validate a value graph without repeatedly visiting shared sublists."""
    pending = [(value, 0)]
    seen: dict[int, int] = {}
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if nodes > limits.max_value_nodes or depth > limits.max_value_depth:
            fail("LimitError", "Value is too large or too deeply nested.", code="Q4007")
        item_type = type(item)
        if item_type is int:
            if item.bit_length() > limits.max_integer_bits:
                fail("LimitError", "Integer result exceeds the configured bit limit.", code="Q4008")
        elif item_type is float:
            if not math.isfinite(item):
                fail("RuntimeError", "Operation produced a non-finite number.", code="Q3005")
        elif item_type is str:
            check_length(len(item), limits.max_string, "Text length")
        elif item_type in (list, dict):
            # Revisit a shared node only when reached through a deeper path.
            if seen.get(id(item), -1) >= depth:
                continue
            seen[id(item)] = depth
            check_length(len(item), limits.max_items, "Collection size")
            if item_type is dict:
                for key in item:
                    text(key)
                    check_length(len(key), limits.max_string, "Map key length")
                pending.extend((child, depth + 1) for child in item.values())
            else:
                pending.extend((child, depth + 1) for child in item)
        elif item_type not in (type(None), bool):
            fail("TypeError", "Unsupported value type.", code="Q3004")


def format_value(value, max_chars: int = 200_000) -> str:
    """Render language spellings, with a work/output budget for shared graphs."""
    parts: list[str] = []
    remaining, visits = max_chars, 0

    def append(part: str):
        nonlocal remaining
        remaining -= len(part)
        if remaining < 0:
            fail("LimitError", "Rendered output is too large.", code="Q4009")
        parts.append(part)

    def visit(item, depth=0):
        nonlocal visits
        visits += 1
        if visits > 100_000 or depth > 50:
            fail("LimitError", "Value is too complex to render.", code="Q4009")
        if item is None:
            append("void")
        elif type(item) is bool:
            append("aye" if item else "nay")
        elif type(item) is str:
            if depth:
                # Reversible quoted representation for collection elements.
                import json
                append(json.dumps(item, ensure_ascii=False))
            else:
                append(item)
        elif type(item) is list:
            append("[")
            for index, child in enumerate(item):
                if index:
                    append(", ")
                visit(child, depth + 1)
            append("]")
        elif type(item) is dict:
            append("{")
            for index, (key, child) in enumerate(item.items()):
                if index:
                    append(", ")
                visit(key, depth + 1)
                append(": ")
                visit(child, depth + 1)
            append("}")
        else:
            append(str(item))
    visit(value)
    return "".join(parts)


def arithmetic(operator, left, right, limits: Limits):
    left, right = number(left), number(right)
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator == "*":
        return left * right
    if operator in {"/", "//", "%"} and right == 0:
        fail("RuntimeError", "Division or remainder by zero is not allowed.", code="Q3002",
             hint="Check that the divisor is not zero before this operation.")
    if operator == "/":
        return left / right
    if operator == "//":
        return left // right
    if operator == "%":
        return left % right
    if operator == "**":
        if abs(right) > 10_000:
            fail("LimitError", "Exponent magnitude exceeds 10,000.", code="Q4010")
        if left < 0 and type(right) is float and not right.is_integer():
            fail("RuntimeError", "Complex numbers are not supported.", code="Q3005")
        if type(left) is int and type(right) is int and right >= 0 and abs(left) > 1:
            if right * math.log2(abs(left)) >= limits.max_integer_bits:
                fail("LimitError", "Power result would exceed the integer limit.", code="Q4008")
        return left ** right
    fail("RuntimeError", f"Unknown arithmetic operator {operator!r}.", code="Q3999")


def pick(values, index):
    values, index = sequence(values), integer(index)
    if not -len(values) <= index < len(values):
        fail("IndexError", f"Index {index} is outside a sequence of length {len(values)}.", code="Q3006")
    return values[index]
