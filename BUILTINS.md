# QWERTY v1: All 80 Built-in Functions

All names below are QWERTY names. They are not aliases injected into the Python interpreter.

Optional arguments below are positional. Keyword arguments are not part of QWERTY v1.

Collection update helpers return new values; assign the result to retain an update.


## Arithmetic

### 1. `addit(a, b)`

Numeric + operation.

```qwerty
addit(8, 2);
```

Returns: `10`.

### 2. `subit(a, b)`

Numeric - operation.

```qwerty
subit(8, 2);
```

Returns: `6`.

### 3. `multit(a, b)`

Numeric * operation.

```qwerty
multit(8, 2);
```

Returns: `16`.

### 4. `divit(a, b)`

Numeric / operation.

```qwerty
divit(8, 2);
```

Returns: `4.0`.

### 5. `floordivit(a, b)`

Numeric // operation.

```qwerty
floordivit(9, 2);
```

Returns: `4`.

### 6. `modit(a, b)`

Numeric % operation.

```qwerty
modit(9, 2);
```

Returns: `1`.

### 7. `powerit(a, b)`

Numeric ** operation.

```qwerty
powerit(2, 3);
```

Returns: `8`.

### 8. `absit(number)`

Absolute value.

```qwerty
absit(-7);
```

Returns: `7`.

### 9. `rootit(number)`

Non-negative square root.

```qwerty
rootit(25);
```

Returns: `5.0`.

### 10. `roundit(number, places=0)`

Round using ties-to-even; places -100..100.

```qwerty
roundit(3.14159, 2);
```

Returns: `3.14`.

### 11. `ceilit(number)`

Round toward positive infinity.

```qwerty
ceilit(2.1);
```

Returns: `3`.

### 12. `floorit(number)`

Round toward negative infinity.

```qwerty
floorit(2.9);
```

Returns: `2`.

### 13. `minit(numbers)`

Smallest number; non-empty list.

```qwerty
minit([3, 1, 2]);
```

Returns: `1`.

### 14. `maxit(numbers)`

Largest number; non-empty list.

```qwerty
maxit([3, 1, 2]);
```

Returns: `3`.

### 15. `sumit(numbers)`

Sum a numeric list; empty list returns zero.

```qwerty
sumit([1, 2, 3]);
```

Returns: `6`.

### 16. `avgit(numbers)`

Arithmetic mean; non-empty numeric list.

```qwerty
avgit([2, 4, 6]);
```

Returns: `4.0`.

### 17. `factorit(integer)`

Factorial of an integer from 0 to 500.

```qwerty
factorit(5);
```

Returns: `120`.

### 18. `gcdit(a, b)`

Greatest common divisor of two integers.

```qwerty
gcdit(12, 18);
```

Returns: `6`.

### 19. `lcmit(a, b)`

Least common multiple of two integers.

```qwerty
lcmit(4, 6);
```

Returns: `12`.

### 20. `clampit(value, low, high)`

Limit a number to an inclusive interval.

```qwerty
clampit(12, 0, 10);
```

Returns: `10`.


## Logic

### 21. `equalit(a, b)`

Structural equality; booleans are distinct from numbers.

```qwerty
equalit(3, 3.0);
```

Returns: `aye`.

### 22. `diffit(a, b)`

Structural inequality.

```qwerty
diffit(3, 4);
```

Returns: `aye`.

### 23. `greaterit(a, b)`

Compare numbers or text with >.

```qwerty
greaterit(3, 2);
```

Returns: `aye`.

### 24. `lessit(a, b)`

Compare numbers or text with <.

```qwerty
lessit(3, 2);
```

Returns: `nay`.

### 25. `atleastit(a, b)`

Compare numbers or text with >=.

```qwerty
atleastit(3, 3);
```

Returns: `aye`.

### 26. `atmostit(a, b)`

Compare numbers or text with <=.

```qwerty
atmostit(4, 3);
```

Returns: `nay`.

### 27. `andit(a, b)`

Eager logical AND; returns a boolean.

```qwerty
andit(aye, nay);
```

Returns: `nay`.

### 28. `orit(a, b)`

Eager logical OR; returns a boolean.

```qwerty
orit(aye, nay);
```

Returns: `aye`.

### 29. `notit(value)`

Logical negation of truthiness.

```qwerty
notit(nay);
```

Returns: `aye`.


## Text

### 30. `concatit(...text)`

Concatenate text arguments without a separator.

```qwerty
concatit("Q", "WERTY");
```

Returns: `"QWERTY"`.

### 31. `upperit(text)`

Text upper operation.

```qwerty
upperit("hello");
```

Returns: `"HELLO"`.

### 32. `lowerit(text)`

Text lower operation.

```qwerty
lowerit("HELLO");
```

Returns: `"hello"`.

### 33. `titleit(text)`

Text title operation.

```qwerty
titleit("hello world");
```

Returns: `"Hello World"`.

### 34. `trimit(text)`

Text strip operation.

```qwerty
trimit("  hello  ");
```

Returns: `"hello"`.

### 35. `ltrimit(text)`

Text lstrip operation.

```qwerty
ltrimit("  hello  ");
```

Returns: `"hello  "`.

### 36. `rtrimit(text)`

Text rstrip operation.

```qwerty
rtrimit("  hello  ");
```

Returns: `"  hello"`.

### 37. `splitit(text, separator=void)`

Split text; default separates whitespace.

```qwerty
splitit("a,b", ",");
```

Returns: `["a", "b"]`.

### 38. `joinit(separator, text_list)`

Join a list of text values.

```qwerty
joinit("-", ["a", "b"]);
```

Returns: `"a-b"`.

### 39. `replaceit(text, old, new)`

Replace all matching substrings.

```qwerty
replaceit("abcabc", "a", "x");
```

Returns: `"xbcxbc"`.

### 40. `findit(text, target)`

First substring index, or -1 when missing.

```qwerty
findit("hello", "ll");
```

Returns: `2`.

### 41. `startsit(text, prefix)`

Test a text prefix.

```qwerty
startsit("hello", "he");
```

Returns: `aye`.

### 42. `endsit(text, suffix)`

Test a text suffix.

```qwerty
endsit("hello", "lo");
```

Returns: `aye`.

### 43. `countit(sequence, target)`

Count non-overlapping substrings or equal list items.

```qwerty
countit("banana", "an");
```

Returns: `2`.

### 44. `repeatit(text, count)`

Repeat text a non-negative integer number of times.

```qwerty
repeatit("ha", 3);
```

Returns: `"hahaha"`.

### 45. `sliceit(sequence, start, stop)`

Copy a slice; stop is excluded, bounds may be negative.

```qwerty
sliceit("hello", 1, 4);
```

Returns: `"ell"`.

### 46. `charit(codepoint)`

Unicode scalar value to a character.

```qwerty
charit(65);
```

Returns: `"A"`.

### 47. `codeit(character)`

A single character to its Unicode codepoint.

```qwerty
codeit("A");
```

Returns: `65`.

### 48. `alphait(text)`

Whether non-empty text contains only Unicode letters.

```qwerty
alphait("hello");
```

Returns: `aye`.

### 49. `digitit(text)`

Whether non-empty text contains only Unicode digits.

```qwerty
digitit("123");
```

Returns: `aye`.


## Lists

### 50. `listit(...values)`

Build a new list from positional values.

```qwerty
listit(1, 2, 3);
```

Returns: `[1, 2, 3]`.

### 51. `sizeit(collection)`

Length of text, a list, or a map.

```qwerty
sizeit([1, 2, 3]);
```

Returns: `3`.

### 52. `pushit(list, value)`

Return a new list with value appended.

```qwerty
pushit([1, 2], 3);
```

Returns: `[1, 2, 3]`.

### 53. `firstit(sequence)`

First item; error for an empty sequence.

```qwerty
firstit([7, 8]);
```

Returns: `7`.

### 54. `lastit(sequence)`

Last item; error for an empty sequence.

```qwerty
lastit([7, 8]);
```

Returns: `8`.

### 55. `pickit(sequence, index)`

Read a zero-based index; negative indices count from the end.

```qwerty
pickit([4, 5, 6], 1);
```

Returns: `5`.

### 56. `putit(list, index, value)`

Return a list with one existing index replaced.

```qwerty
putit([1, 2], 0, 9);
```

Returns: `[9, 2]`.

### 57. `popit(list)`

Return a list without its last item; does not return that item.

```qwerty
popit([1, 2, 3]);
```

Returns: `[1, 2]`.

### 58. `removeit(list, value)`

Return a list with its first matching value removed.

```qwerty
removeit([1, 2, 1], 1);
```

Returns: `[2, 1]`.

### 59. `sortit(list, descending=nay)`

Return a sorted numeric or text list.

```qwerty
sortit([3, 1, 2]);
```

Returns: `[1, 2, 3]`.

### 60. `reverseit(sequence)`

Return reversed text or a reversed list.

```qwerty
reverseit([1, 2, 3]);
```

Returns: `[3, 2, 1]`.

### 61. `uniqueit(list)`

Remove duplicates, preserving first occurrence order.

```qwerty
uniqueit([1, 2, 1, 3]);
```

Returns: `[1, 2, 3]`.

### 62. `spanit(stop) or spanit(start, stop, step=1)`

Integer range as a list; stop excluded; step cannot be zero.

```qwerty
spanit(1, 6, 2);
```

Returns: `[1, 3, 5]`.

### 63. `mergeit(list_a, list_b)`

Concatenate two lists into a new list.

```qwerty
mergeit([1, 2], [3]);
```

Returns: `[1, 2, 3]`.

### 64. `emptyit(collection)`

Whether text, a list, or a map has zero items.

```qwerty
emptyit([]);
```

Returns: `aye`.


## Maps

### 65. `mapit(keys, values)`

Build a map; duplicate keys use the last value.

```qwerty
mapit(["a", "b"], [1, 2]);
```

Returns: `{"a": 1, "b": 2}`.

### 66. `getit(map, key, default=void)`

Read a key, returning default if absent.

```qwerty
getit(mapit(["a"], [1]), "a");
```

Returns: `1`.

### 67. `setit(map, key, value)`

Return a map with a key inserted or replaced.

```qwerty
setit(mapit([], []), "a", 1);
```

Returns: `{"a": 1}`.

### 68. `keysit(map)`

Keys in insertion order.

```qwerty
keysit(mapit(["a", "b"], [1, 2]));
```

Returns: `["a", "b"]`.

### 69. `valuesit(map)`

Values in insertion order.

```qwerty
valuesit(mapit(["a", "b"], [1, 2]));
```

Returns: `[1, 2]`.

### 70. `hasit(collection, value)`

Test a map key, substring, or equal list item.

```qwerty
hasit(mapit(["a"], [1]), "a");
```

Returns: `aye`.


## Types

### 71. `textit(value)`

Convert to QWERTY display text.

```qwerty
textit(aye);
```

Returns: `"aye"`.

### 72. `intit(value)`

Numeric text or number to an integer; decimals truncate toward zero.

```qwerty
intit("42");
```

Returns: `42`.

### 73. `floatit(value)`

Numeric text or number to a finite decimal.

```qwerty
floatit("3.5");
```

Returns: `3.5`.

### 74. `boolit(value)`

Truthiness conversion; non-empty text including 'nay' is true.

```qwerty
boolit(0);
```

Returns: `nay`.

### 75. `typeit(value)`

Return void/boolean/integer/decimal/text/list/map.

```qwerty
typeit("hello");
```

Returns: `"text"`.

### 76. `isnumit(value)`

Test for integer or decimal; excludes booleans.

```qwerty
isnumit(3.5);
```

Returns: `aye`.

### 77. `istextit(value)`

Test for a text value.

```qwerty
istextit("hello");
```

Returns: `aye`.


## I/O

### 78. `sayit(...values)`

Print values separated by spaces and end with a newline; return void.

```qwerty
sayit("hello");
```

Returns: `void`.

The example also writes `hello` followed by a newline.

### 79. `askit(prompt="")`

Write a prompt and consume one input line as text.

```qwerty
askit("Name: ");
```

Returns: `"Ada"`.

This result assumes the next input line is `Ada`; the prompt is also written to output.

### 80. `assertit(condition, message="Assertion failed.")`

Raise an assertion error if condition is false; otherwise return void.

```qwerty
assertit(aye, "failed");
```

Returns: `void`.
