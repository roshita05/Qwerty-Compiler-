"""The complete QWERTY standard library: 80 custom-named functions.

Implementations are Python callables, but QWERTY can only call this explicit
registry. There is no route from a QWERTY identifier to arbitrary Python APIs.
Collection update functions return new values and never mutate their inputs.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
import math
from .context import Context
from .errors import fail
from .values import (arithmetic, array, boolean, check_length, collection, equal,
                     format_value, integer, kind, mapping, number, ordered, pick,
                     sequence, text)


@dataclass(frozen=True)
class Builtin:
    name: str
    signature: str
    category: str
    minimum: int
    maximum: int
    description: str
    example: str
    expected: Any
    implementation: Callable

    def accepts(self, count: int) -> bool:
        return self.minimum <= count <= self.maximum

    def arity_description(self) -> str:
        return str(self.minimum) if self.minimum == self.maximum else f"{self.minimum}..{self.maximum}"


REGISTRY: dict[str, Builtin] = {}


def register(name, signature, category, minimum, maximum, description, example, expected, implementation):
    if name in REGISTRY:
        raise ValueError(f"Duplicate built-in {name}")
    REGISTRY[name] = Builtin(name, signature, category, minimum, maximum,
                             description, example, expected, implementation)


def numeric_list(values, nonempty=False):
    values = array(values)
    if nonempty and not values:
        fail("RuntimeError", "This operation requires a non-empty list.", code="Q3008")
    return [number(value) for value in values]


def do_round(ctx, value, places=0):
    value, places = number(value), integer(places)
    if abs(places) > 100:
        fail("LimitError", "roundit() accepts between -100 and 100 places.", code="Q4010")
    return round(value, places)


def do_factor(ctx, value):
    value = integer(value)
    if not 0 <= value <= 500:
        fail("RuntimeError", "factorit() requires an integer from 0 to 500.", code="Q3008")
    return math.factorial(value)


def do_clamp(ctx, value, low, high):
    value, low, high = number(value), number(low), number(high)
    if low > high:
        fail("RuntimeError", "clampit() lower bound must not exceed its upper bound.", code="Q3008")
    return min(max(value, low), high)


def do_concat(ctx, *values):
    values = [text(value) for value in values]
    check_length(sum(map(len, values)), ctx.limits.max_string, "Text length")
    return "".join(values)


def do_split(ctx, value, separator=None):
    value = text(value)
    if separator is not None:
        separator = text(separator)
        if not separator:
            fail("RuntimeError", "splitit() separator cannot be empty.", code="Q3008")
    # Limit the allocation even when there are many separators.
    result = value.split(separator, ctx.limits.max_items)
    check_length(len(result), ctx.limits.max_items, "Split result")
    return result


def do_join(ctx, separator, values):
    separator = text(separator)
    values = [text(value) for value in array(values)]
    length = sum(map(len, values)) + max(0, len(values) - 1) * len(separator)
    check_length(length, ctx.limits.max_string, "Text length")
    return separator.join(values)


def do_replace(ctx, value, old, new):
    value, old, new = text(value), text(old), text(new)
    length = len(value) + value.count(old) * (len(new) - len(old))
    check_length(length, ctx.limits.max_string, "Text length")
    return value.replace(old, new)


def do_count(ctx, values, target):
    values = sequence(values)
    if type(values) is str:
        return values.count(text(target))
    return sum(1 for value in values if equal(value, target))


def do_repeat(ctx, value, count):
    value, count = text(value), integer(count)
    if count < 0:
        fail("RuntimeError", "repeatit() count must be non-negative.", code="Q3008")
    check_length(len(value) * count, ctx.limits.max_string, "Text length")
    return value * count


def do_char(ctx, value):
    value = integer(value)
    if not 0 <= value <= 0x10FFFF or 0xD800 <= value <= 0xDFFF:
        fail("RuntimeError", "charit() requires a valid Unicode scalar value.", code="Q3008")
    return chr(value)


def do_code(ctx, value):
    value = text(value)
    if len(value) != 1:
        fail("RuntimeError", "codeit() needs exactly one character.", code="Q3008")
    return ord(value)


def do_push(ctx, values, value):
    values = array(values)
    check_length(len(values) + 1, ctx.limits.max_items, "List size")
    return values + [value]


def do_put(ctx, values, index, value):
    values, index = array(values), integer(index)
    pick(values, index)
    result = values.copy()
    result[index] = value
    return result


def do_pop(ctx, values):
    values = array(values)
    pick(values, -1)
    return values[:-1]


def do_remove(ctx, values, value):
    values = array(values)
    for index, item in enumerate(values):
        ctx.check_time()
        if equal(item, value):
            return values[:index] + values[index + 1:]
    fail("RuntimeError", "removeit() could not find the requested value.", code="Q3008")


def do_sort(ctx, values, descending=False):
    values, descending = array(values), boolean(descending)
    if values and not (all(type(v) in (int, float) for v in values) or all(type(v) is str for v in values)):
        fail("TypeError", "sortit() needs a list of numbers or a list of text values.", code="Q3004")
    return sorted(values, reverse=descending)


def do_unique(ctx, values):
    result = []
    for item in array(values):
        ctx.check_time()
        if not any(equal(item, other) for other in result):
            result.append(item)
    return result


def do_span(ctx, *values):
    result = range(*(integer(value) for value in values))
    try:
        count = len(result)
    except OverflowError:
        fail("LimitError", "spanit() result is too large.", code="Q4006")
    check_length(count, ctx.limits.max_items, "Range size")
    return list(result)


def do_merge(ctx, left, right):
    left, right = array(left), array(right)
    check_length(len(left) + len(right), ctx.limits.max_items, "List size")
    return left + right


def do_map(ctx, keys, values):
    keys, values = array(keys), array(values)
    if len(keys) != len(values):
        fail("RuntimeError", "mapit() needs equally sized key and value lists.", code="Q3008")
    return {text(key): value for key, value in zip(keys, values)}


def do_set(ctx, values, key, value):
    values, key = mapping(values), text(key)
    check_length(len(values) + (key not in values), ctx.limits.max_items, "Map size")
    result = values.copy()
    result[key] = value
    return result


def do_has(ctx, values, value):
    values = collection(values)
    if type(values) in (str, dict):
        return text(value) in values
    return any(equal(value, item) for item in values)


def do_int(ctx, value):
    if type(value) not in (int, float, str):
        fail("TypeError", "intit() accepts a number or numeric text, not a boolean.", code="Q3004")
    if type(value) is str and len(value.strip()) > 1_200:
        fail("LimitError", "Numeric text is too long.", code="Q4008")
    return int(value)


def do_float(ctx, value):
    if type(value) not in (int, float, str):
        fail("TypeError", "floatit() accepts a number or numeric text, not a boolean.", code="Q3004")
    return float(value)


def do_say(ctx, *values):
    remaining = ctx.limits.max_output - ctx.output_size
    parts = []
    for value in values:
        part = format_value(value, remaining)
        remaining -= len(part) + 1
        parts.append(part)
    ctx.emit(" ".join(parts) + "\n")
    return None


def do_assert(ctx, condition, message="Assertion failed."):
    message = text(message)
    if not condition:
        fail("AssertionError", message, code="Q3009")
    return None


# Arithmetic: 20 functions.
for name, operator, example, expected in [
    ("addit", "+", "addit(8, 2)", 10), ("subit", "-", "subit(8, 2)", 6),
    ("multit", "*", "multit(8, 2)", 16), ("divit", "/", "divit(8, 2)", 4.0),
    ("floordivit", "//", "floordivit(9, 2)", 4), ("modit", "%", "modit(9, 2)", 1),
    ("powerit", "**", "powerit(2, 3)", 8),
]:
    register(name, f"{name}(a, b)", "Arithmetic", 2, 2, f"Numeric {operator} operation.", example, expected,
             lambda ctx, a, b, op=operator: arithmetic(op, a, b, ctx.limits))
register("absit", "absit(number)", "Arithmetic", 1, 1, "Absolute value.", "absit(-7)", 7, lambda c, x: abs(number(x)))
register("rootit", "rootit(number)", "Arithmetic", 1, 1, "Non-negative square root.", "rootit(25)", 5.0, lambda c, x: math.sqrt(number(x)))
register("roundit", "roundit(number, places=0)", "Arithmetic", 1, 2, "Round using ties-to-even; places -100..100.", "roundit(3.14159, 2)", 3.14, do_round)
register("ceilit", "ceilit(number)", "Arithmetic", 1, 1, "Round toward positive infinity.", "ceilit(2.1)", 3, lambda c, x: math.ceil(number(x)))
register("floorit", "floorit(number)", "Arithmetic", 1, 1, "Round toward negative infinity.", "floorit(2.9)", 2, lambda c, x: math.floor(number(x)))
register("minit", "minit(numbers)", "Arithmetic", 1, 1, "Smallest number; non-empty list.", "minit([3, 1, 2])", 1, lambda c, x: min(numeric_list(x, True)))
register("maxit", "maxit(numbers)", "Arithmetic", 1, 1, "Largest number; non-empty list.", "maxit([3, 1, 2])", 3, lambda c, x: max(numeric_list(x, True)))
register("sumit", "sumit(numbers)", "Arithmetic", 1, 1, "Sum a numeric list; empty list returns zero.", "sumit([1, 2, 3])", 6, lambda c, x: sum(numeric_list(x)))
register("avgit", "avgit(numbers)", "Arithmetic", 1, 1, "Arithmetic mean; non-empty numeric list.", "avgit([2, 4, 6])", 4.0, lambda c, x: sum(numeric_list(x, True)) / len(x))
register("factorit", "factorit(integer)", "Arithmetic", 1, 1, "Factorial of an integer from 0 to 500.", "factorit(5)", 120, do_factor)
register("gcdit", "gcdit(a, b)", "Arithmetic", 2, 2, "Greatest common divisor of two integers.", "gcdit(12, 18)", 6, lambda c, a, b: math.gcd(integer(a), integer(b)))
register("lcmit", "lcmit(a, b)", "Arithmetic", 2, 2, "Least common multiple of two integers.", "lcmit(4, 6)", 12, lambda c, a, b: math.lcm(integer(a), integer(b)))
register("clampit", "clampit(value, low, high)", "Arithmetic", 3, 3, "Limit a number to an inclusive interval.", "clampit(12, 0, 10)", 10, do_clamp)

# Comparison and logic: 9 functions. andit/orit are eager; &&/|| short-circuit.
register("equalit", "equalit(a, b)", "Logic", 2, 2, "Structural equality; booleans are distinct from numbers.", "equalit(3, 3.0)", True, lambda c, a, b: equal(a, b))
register("diffit", "diffit(a, b)", "Logic", 2, 2, "Structural inequality.", "diffit(3, 4)", True, lambda c, a, b: not equal(a, b))
for name, operator, example, expected in [
    ("greaterit", ">", "greaterit(3, 2)", True), ("lessit", "<", "lessit(3, 2)", False),
    ("atleastit", ">=", "atleastit(3, 3)", True), ("atmostit", "<=", "atmostit(4, 3)", False),
]:
    register(name, f"{name}(a, b)", "Logic", 2, 2, f"Compare numbers or text with {operator}.", example, expected,
             lambda c, a, b, op=operator: ordered(a, b, op))
register("andit", "andit(a, b)", "Logic", 2, 2, "Eager logical AND; returns a boolean.", "andit(aye, nay)", False, lambda c, a, b: bool(a) and bool(b))
register("orit", "orit(a, b)", "Logic", 2, 2, "Eager logical OR; returns a boolean.", "orit(aye, nay)", True, lambda c, a, b: bool(a) or bool(b))
register("notit", "notit(value)", "Logic", 1, 1, "Logical negation of truthiness.", "notit(nay)", True, lambda c, x: not x)

# Text and sequence helpers: 20 functions.
register("concatit", "concatit(...text)", "Text", 0, 256, "Concatenate text arguments without a separator.", 'concatit("Q", "WERTY")', "QWERTY", do_concat)
for name, method, example, expected in [
    ("upperit", str.upper, 'upperit("hello")', "HELLO"),
    ("lowerit", str.lower, 'lowerit("HELLO")', "hello"),
    ("titleit", str.title, 'titleit("hello world")', "Hello World"),
    ("trimit", str.strip, 'trimit("  hello  ")', "hello"),
    ("ltrimit", str.lstrip, 'ltrimit("  hello  ")', "hello  "),
    ("rtrimit", str.rstrip, 'rtrimit("  hello  ")', "  hello"),
]:
    register(name, f"{name}(text)", "Text", 1, 1, f"Text {method.__name__} operation.", example, expected,
             lambda c, x, action=method: action(text(x)))
register("splitit", "splitit(text, separator=void)", "Text", 1, 2, "Split text; default separates whitespace.", 'splitit("a,b", ",")', ["a", "b"], do_split)
register("joinit", "joinit(separator, text_list)", "Text", 2, 2, "Join a list of text values.", 'joinit("-", ["a", "b"])', "a-b", do_join)
register("replaceit", "replaceit(text, old, new)", "Text", 3, 3, "Replace all matching substrings.", 'replaceit("abcabc", "a", "x")', "xbcxbc", do_replace)
register("findit", "findit(text, target)", "Text", 2, 2, "First substring index, or -1 when missing.", 'findit("hello", "ll")', 2, lambda c, x, y: text(x).find(text(y)))
register("startsit", "startsit(text, prefix)", "Text", 2, 2, "Test a text prefix.", 'startsit("hello", "he")', True, lambda c, x, y: text(x).startswith(text(y)))
register("endsit", "endsit(text, suffix)", "Text", 2, 2, "Test a text suffix.", 'endsit("hello", "lo")', True, lambda c, x, y: text(x).endswith(text(y)))
register("countit", "countit(sequence, target)", "Text", 2, 2, "Count non-overlapping substrings or equal list items.", 'countit("banana", "an")', 2, do_count)
register("repeatit", "repeatit(text, count)", "Text", 2, 2, "Repeat text a non-negative integer number of times.", 'repeatit("ha", 3)', "hahaha", do_repeat)
register("sliceit", "sliceit(sequence, start, stop)", "Text", 3, 3, "Copy a slice; stop is excluded, bounds may be negative.", 'sliceit("hello", 1, 4)', "ell", lambda c, x, a, b: sequence(x)[integer(a):integer(b)])
register("charit", "charit(codepoint)", "Text", 1, 1, "Unicode scalar value to a character.", "charit(65)", "A", do_char)
register("codeit", "codeit(character)", "Text", 1, 1, "A single character to its Unicode codepoint.", 'codeit("A")', 65, do_code)
register("alphait", "alphait(text)", "Text", 1, 1, "Whether non-empty text contains only Unicode letters.", 'alphait("hello")', True, lambda c, x: text(x).isalpha())
register("digitit", "digitit(text)", "Text", 1, 1, "Whether non-empty text contains only Unicode digits.", 'digitit("123")', True, lambda c, x: text(x).isdigit())

# Lists: 15 functions. All update operations return new lists.
register("listit", "listit(...values)", "Lists", 0, 256, "Build a new list from positional values.", "listit(1, 2, 3)", [1, 2, 3], lambda c, *x: list(x))
register("sizeit", "sizeit(collection)", "Lists", 1, 1, "Length of text, a list, or a map.", "sizeit([1, 2, 3])", 3, lambda c, x: len(collection(x)))
register("pushit", "pushit(list, value)", "Lists", 2, 2, "Return a new list with value appended.", "pushit([1, 2], 3)", [1, 2, 3], do_push)
register("firstit", "firstit(sequence)", "Lists", 1, 1, "First item; error for an empty sequence.", "firstit([7, 8])", 7, lambda c, x: pick(x, 0))
register("lastit", "lastit(sequence)", "Lists", 1, 1, "Last item; error for an empty sequence.", "lastit([7, 8])", 8, lambda c, x: pick(x, -1))
register("pickit", "pickit(sequence, index)", "Lists", 2, 2, "Read a zero-based index; negative indices count from the end.", "pickit([4, 5, 6], 1)", 5, lambda c, x, i: pick(x, i))
register("putit", "putit(list, index, value)", "Lists", 3, 3, "Return a list with one existing index replaced.", "putit([1, 2], 0, 9)", [9, 2], do_put)
register("popit", "popit(list)", "Lists", 1, 1, "Return a list without its last item; does not return that item.", "popit([1, 2, 3])", [1, 2], do_pop)
register("removeit", "removeit(list, value)", "Lists", 2, 2, "Return a list with its first matching value removed.", "removeit([1, 2, 1], 1)", [2, 1], do_remove)
register("sortit", "sortit(list, descending=nay)", "Lists", 1, 2, "Return a sorted numeric or text list.", "sortit([3, 1, 2])", [1, 2, 3], do_sort)
register("reverseit", "reverseit(sequence)", "Lists", 1, 1, "Return reversed text or a reversed list.", "reverseit([1, 2, 3])", [3, 2, 1], lambda c, x: sequence(x)[::-1])
register("uniqueit", "uniqueit(list)", "Lists", 1, 1, "Remove duplicates, preserving first occurrence order.", "uniqueit([1, 2, 1, 3])", [1, 2, 3], do_unique)
register("spanit", "spanit(stop) or spanit(start, stop, step=1)", "Lists", 1, 3, "Integer range as a list; stop excluded; step cannot be zero.", "spanit(1, 6, 2)", [1, 3, 5], do_span)
register("mergeit", "mergeit(list_a, list_b)", "Lists", 2, 2, "Concatenate two lists into a new list.", "mergeit([1, 2], [3])", [1, 2, 3], do_merge)

register("emptyit", "emptyit(collection)", "Lists", 1, 1, "Whether text, a list, or a map has zero items.", "emptyit([])", True, lambda c, x: len(collection(x)) == 0)

# Maps: 6 functions. Keys must be text.
register("mapit", "mapit(keys, values)", "Maps", 2, 2, "Build a map; duplicate keys use the last value.", 'mapit(["a", "b"], [1, 2])', {"a": 1, "b": 2}, do_map)
register("getit", "getit(map, key, default=void)", "Maps", 2, 3, "Read a key, returning default if absent.", 'getit(mapit(["a"], [1]), "a")', 1, lambda c, x, k, d=None: mapping(x).get(text(k), d))
register("setit", "setit(map, key, value)", "Maps", 3, 3, "Return a map with a key inserted or replaced.", 'setit(mapit([], []), "a", 1)', {"a": 1}, do_set)
register("keysit", "keysit(map)", "Maps", 1, 1, "Keys in insertion order.", 'keysit(mapit(["a", "b"], [1, 2]))', ["a", "b"], lambda c, x: list(mapping(x)))
register("valuesit", "valuesit(map)", "Maps", 1, 1, "Values in insertion order.", 'valuesit(mapit(["a", "b"], [1, 2]))', [1, 2], lambda c, x: list(mapping(x).values()))
register("hasit", "hasit(collection, value)", "Maps", 2, 2, "Test a map key, substring, or equal list item.", 'hasit(mapit(["a"], [1]), "a")', True, do_has)

# Conversions and type inspection: 7 functions.
register("textit", "textit(value)", "Types", 1, 1, "Convert to QWERTY display text.", "textit(aye)", "aye", lambda c, x: format_value(x, c.limits.max_string))
register("intit", "intit(value)", "Types", 1, 1, "Numeric text or number to an integer; decimals truncate toward zero.", 'intit("42")', 42, do_int)
register("floatit", "floatit(value)", "Types", 1, 1, "Numeric text or number to a finite decimal.", 'floatit("3.5")', 3.5, do_float)
register("boolit", "boolit(value)", "Types", 1, 1, "Truthiness conversion; non-empty text including 'nay' is true.", "boolit(0)", False, lambda c, x: bool(x))
register("typeit", "typeit(value)", "Types", 1, 1, "Return void/boolean/integer/decimal/text/list/map.", 'typeit("hello")', "text", lambda c, x: kind(x))
register("isnumit", "isnumit(value)", "Types", 1, 1, "Test for integer or decimal; excludes booleans.", "isnumit(3.5)", True, lambda c, x: type(x) in (int, float))
register("istextit", "istextit(value)", "Types", 1, 1, "Test for a text value.", 'istextit("hello")', True, lambda c, x: type(x) is str)

# Input/output and assertions: 3 functions.
register("sayit", "sayit(...values)", "I/O", 0, 256, "Print values separated by spaces and end with a newline; return void.", 'sayit("hello")', None, do_say)
register("askit", "askit(prompt=\"\")", "I/O", 0, 1, "Write a prompt and consume one input line as text.", 'askit("Name: ")', "Ada", lambda c, prompt="": c.read(prompt))
register("assertit", "assertit(condition, message=\"Assertion failed.\")", "I/O", 1, 2, "Raise an assertion error if condition is false; otherwise return void.", 'assertit(aye, "failed")', None, do_assert)
