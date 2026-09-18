# QWERTY Compiler

**User guide**

<img width="944" height="470" alt="image" src="https://github.com/user-attachments/assets/0a79dffb-d3de-49b4-8914-d38c9b699032" />
<img width="943" height="468" alt="image" src="https://github.com/user-attachments/assets/faaa212e-dee8-411a-bdc6-b41cdf8dcd90" />


**Edition:** 1.1 browser deployment, with the original v1 Python language engine.  
**Prepared:** 18 September 2026.  
**Built-in functions:** exactly 80.  
**Audience:** first-time QWERTY users and the person deploying this project.

> **The most important rule:** `addit(8, 2);` calculates and returns `10` but does not print it. Write **`sayit(addit(8, 2));`** to display `10` in the Console. This is expected language behavior, not a failed calculation.

## Contents

- [1. What the project does](#1-what-the-project-does)
- [2. Start using QWERTY](#2-start-using-qwerty)
- [3. Language essentials](#3-language-essentials)
- [4. Working examples](#4-working-examples)


## 1. What the project does

QWERTY is a small custom programming language implemented in Python. Its grammar, lexer, parser, compiler, instruction format, virtual machine, and 80-function standard library belong to this project. Supporting 80 built-ins does **not** mean supporting 80 different programming languages.

```text
QWERTY source (.qw)
  -> lexer
  -> parser / syntax tree
  -> compiler / QWERTY instructions
  -> QWERTY virtual machine
  -> console output or a source-located diagnostic
```

This is not native machine-code compilation and does not produce a standalone Windows executable. The original command-line tools can save `.qbc` instruction files for the included VM.

### The hosted architecture

```text
Vercel: serves public/ as a static website
  -> visitor opens the editor
  -> a module Web Worker loads a pinned Pyodide runtime
  -> the worker loads the original Python QWERTY compiler
  -> the visitor's QWERTY program runs inside that worker
  -> the worker returns output / diagnostics / bytecode to the page
```

Pyodide provides Python in the browser and supports running it in a module worker. The project loads its own Python package and calls a fixed bridge function. [1][2]

**The language engine is still Python.** It has not been rewritten in JavaScript. JavaScript handles the editor, worker lifecycle, and messages. This deployment uses no Python Vercel Function and no public `/api/execute` endpoint.

The original localhost editor remains available separately through `py -3 -m qwerty web`. Its files live in `web/`; Vercel serves the new hosted editor in `public/`. Do not deploy the old `web/` directory by itself: it expects a local Python backend.

## 2. Start using QWERTY

### Your first successful run

Open the deployed site, replace the editor contents with this code, and select **Run code**:

```qwerty
sayit("Hello, QWERTY!");
sayit("Addition:", addit(8, 2));
sayit("Subtraction:", subit(8, 2));
```

Expected output:

```text
Hello, QWERTY!
Addition: 10
Subtraction: 6
```

On the first run, the page must download and initialize Python. Keep the tab open while the status says it is loading. Later runs in the same page reuse the runtime; a refresh or Stop starts a fresh worker. The runtime version is pinned to Pyodide `314.0.7`, served from its documented jsDelivr distribution. [1]

### Editor controls

| Control | What it does |
|---|---|
| Source editor | Accepts QWERTY source, not ordinary Python. |
| Run code | Compiles the whole program, then executes it. Ctrl+Enter is a shortcut; Command+Enter also works. |
| Check | Checks parsing, names, call argument counts, and control flow without executing. It is not a complete static type checker. |
| Stop | Terminates the browser worker. A stopped run's unfinished output is not preserved. Run again to load a fresh worker. |
| Console | Shows text produced by `sayit()` and prompts produced by `askit()`. |
| Bytecode | Shows the generated QWERTY instructions, not Python source or an executable file. |
| Program input | Supply input before running: one line per `askit()` call. |
| Function list | Search the 80 built-ins; clicking inserts a complete example at the cursor. Most hosted examples include `sayit()` so they print a result. |
| Examples | Replaces the current program after confirmation. Save a copy before switching. |
| Save .qw | Downloads the source as a file on your computer. It does not save output or program input. |
| User guide | Opens a readable guide containing all 80 functions. The Markdown version can also be downloaded. |

The editor attempts to save its source draft in your browser's local storage. This is not an account, a database, or a backup. Clearing browser data, changing device/site address, private browsing restrictions, or disabling storage can remove or prevent this draft. Save important source with **Save .qw**.

### Returning versus printing

```qwerty
addit(8, 2);               # Calculate and discard the result: no printed output.
keep answer = addit(8, 2); # Calculate and retain the result: still no output.
sayit(answer);            # Print the saved result: 10.
```

Do not replace all function calls with print operations. You need returned values for assignments, conditions, and nested calculations:

```qwerty
keep result = multit(addit(2, 3), 4);
sayit(result);  # 20
```

`sayit()` already prints and returns `void`. `sayit(sayit("Hello"));` prints `Hello` and then `void`, which is usually not intended. Successful `assertit()` also returns `void` and is deliberately silent.

## 3. Language essentials

### Statements, spelling, and values

End simple statements with `;`. Use `{ ... }` for blocks. A line break or indentation alone does not create a block. Names are case-sensitive: `addit` is not `Addit`.

```qwerty
keep score = 10;
score = addit(score, 5);
sayit(score);
```

Use `keep` only for the first declaration in a scope. Reusing `keep` for the same name in that scope raises an error. Variable names begin with an ASCII letter or underscore, followed by letters, digits, or underscores; names beginning with `__` are disallowed. Function names cannot be reused as variable or parameter names.

| Purpose | QWERTY spelling |
|---|---|
| Declare a variable | `keep` |
| Define a function | `craft` |
| Return a value | `give` |
| Conditional branches | `when`, `otherwise` |
| While loop | `whilst` |
| Iterate a collection | `each ... over ...` |
| Exit / continue a loop | `stop;`, `skip;` |
| True / false / null | `aye`, `nay`, `void` |

Integers, decimals, text, booleans, lists, maps, and `void` are supported. Quote text with single or double quotes. Write `0.5`, not `.5`. Use `#` for a line comment or `/* ... */` for a block comment. `//` means floor division, not a comment.

`\n` inside a string represents a newline; a string cannot continue across physical lines. Maps are created with `mapit()`, not a `{key: value}` literal. Curly braces in source describe blocks.

### Strict types and conversion

Text does not silently become a number. `addit("8", 2)` raises a TypeError. Convert it:

```qwerty
sayit(addit(intit("8"), 2));
sayit(concatit("Score: ", textit(42)));
```

Optional arguments shown in signatures are **positional**. Write `roundit(3.14159, 2)`, not `roundit(3.14159, places=2)`. The `...values` notation means several positional arguments; it is not syntax to paste into your program. Variadic built-ins in this version accept at most 256 arguments.

### Conditions and loops

```qwerty
keep score = 85;
when score >= 80 {
    sayit("Passed");
} otherwise {
    sayit("Try again");
}

each number over spanit(1, 4) {
    sayit(number);
}
```

The loop prints `1`, `2`, and `3`. **`spanit()` excludes its stop bound.**

```qwerty
keep counter = 0;
whilst counter < 5 {
    counter = addit(counter, 1);
    when counter == 2 { skip; }
    when counter == 4 { stop; }
    sayit(counter);
}
```

This loop prints `1` and `3`. Always update the condition of a `whilst` loop so it can finish.

For safe conditional evaluation, use `&&` and `||`. These can skip an unnecessary right-hand expression. `andit()` and `orit()` are ordinary function calls, so **both arguments are evaluated first**.

```qwerty
keep denominator = 0;
when denominator != 0 && divit(10, denominator) > 1 {
    sayit("Large result");
}
```

Use `0 < x && x < 10` for a range test; Python-style chained comparisons are not a QWERTY feature. False values are `void`, `nay`, zero, empty text, an empty list, and an empty map. In particular, `boolit("nay")` is `aye`: non-empty text is true.

### Your own functions

```qwerty
craft squareit(number) {
    give multit(number, number);
}

sayit(squareit(6));
```

Output is `36`. Define `craft` functions at the top level, not inside other functions or blocks. They support positional arguments and recursion, but not user-defined default parameters, closures, callbacks, or keyword arguments. A function with no executed `give value;` returns `void`.

### Collections: save the new value

```qwerty
keep items = [10, 20];
items = pushit(items, 30);
items = putit(items, 0, 99);
sayit(items);

keep person = mapit(["name", "age"], ["Ada", 25]);
person = setit(person, "age", 26);
sayit(getit(person, "age"));
```

Output:

```text
[99, 20, 30]
26
```

Update helpers return new collections. A standalone `pushit(items, 30);` does not modify `items`. `popit()` returns the shortened list, **not the removed item**. Indices start at zero; `-1` selects the last element. Use `getit()` for map lookup rather than indexed map access.

## 4. Working examples

### Input: no popup is expected

Place these two lines in **Program input** before running:

```text
Ada
25
```

Then run:

```qwerty
keep name = askit("Your name: ");
sayit(name);
keep age = intit(askit("Your age: "));
sayit(age);
sayit(concatit("Hello, ", name, "!"));
sayit("Next year:", addit(age, 1));
```

Output:

```text
Your name: Ada
Your age: 25
Hello, Ada!
Next year: 26
```

`askit()` returns text and writes its prompt without a newline. The following `sayit()` lines in this example echo each value and end the line. Each Run starts consuming the supplied input from the first line again; unused lines are ignored. An empty input box provides no lines, and an exhausted input list raises an InputError.

### Analyze a list

```qwerty
keep marks = [78, 92, 85, 92, 66];
sayit("Total:", sumit(marks));
sayit("Average:", avgit(marks));
sayit("Highest:", maxit(marks));
sayit("Unique:", uniqueit(marks));
sayit("Descending:", sortit(marks, aye));
```

Output:

```text
Total: 413
Average: 82.6
Highest: 92
Unique: [78, 92, 85, 66]
Descending: [92, 92, 85, 78, 66]
```

### Show a successful assertion

```qwerty
assertit(equalit(addit(2, 3), 5), "Addition should be five.");
sayit("Assertion passed");
```

Output is `Assertion passed`. Without the final `sayit()`, success would produce no output. An assertion failure stops the program; there is no `try`/`catch` syntax in this version.



### Supported versus not supported

Included: custom functions, named calls, variables, branches, loops, recursion, numeric/text/list/map values, source-located diagnostics, checking, bytecode display, and the 80 built-ins below.

Not included: arbitrary Python execution, Python package imports from QWERTY, network or disk APIs in the QWERTY language, classes, user-defined exception handling, a step debugger, cloud accounts, shared workspaces, saved execution history, or native executable generation. Decimal values use floating-point arithmetic, not exact financial decimal arithmetic.

Complete reference: all 80 built-in functions

Every function below comes from the project's actual `qwerty/builtins.py` registry. The printable examples are generated by the documentation generator using the Python engine; their console outputs are captured rather than inferred.

**Signature notation is descriptive:** `places=0`, `default=void`, and similar expressions identify defaults, not supported keyword-call syntax. Call all arguments positionally. Returned text values are shown quoted in the reference; `sayit()` prints top-level text without those surrounding quotes.

| Category | Functions |
|---|---:|
| Arithmetic | 20 |
| Logic | 9 |
| Text | 20 |
| Lists | 15 |
| Maps | 6 |
| Types | 7 |
| I/O | 3 |
| **Total** | **80** |

### Arithmetic

#### 01. `addit(a, b)`

Numeric + operation.

```qwerty
sayit(addit(8, 2));
```

**Console output:**

```text
10
```

**Function return value:** `10`.

**User note:** Both arguments must be numbers. Text such as "8" is not converted automatically; use intit() or floatit() first.

#### 02. `subit(a, b)`

Numeric - operation.

```qwerty
sayit(subit(8, 2));
```

**Console output:**

```text
6
```

**Function return value:** `6`.

**User note:** Subtracts the second number from the first. Reversing the arguments changes the sign.

#### 03. `multit(a, b)`

Numeric * operation.

```qwerty
sayit(multit(8, 2));
```

**Console output:**

```text
16
```

**Function return value:** `16`.

**User note:** Multiplies two numbers. Use repeatit() to repeat text; numeric multiplication does not accept text.

#### 04. `divit(a, b)`

Numeric / operation.

```qwerty
sayit(divit(8, 2));
```

**Console output:**

```text
4.0
```

**Function return value:** `4.0`.

**User note:** Returns a decimal even when the division is exact. A zero divisor raises a runtime error.

#### 05. `floordivit(a, b)`

Numeric // operation.

```qwerty
sayit(floordivit(9, 2));
```

**Console output:**

```text
4
```

**Function return value:** `4`.

**User note:** Floors toward negative infinity, not toward zero. floordivit(-9, 2) returns -5. The divisor cannot be zero.

#### 06. `modit(a, b)`

Numeric % operation.

```qwerty
sayit(modit(9, 2));
```

**Console output:**

```text
1
```

**Function return value:** `1`.

**User note:** Returns the remainder. With negative operands it follows floor-division semantics; the divisor cannot be zero.

#### 07. `powerit(a, b)`

Numeric ** operation.

```qwerty
sayit(powerit(2, 3));
```

**Console output:**

```text
8
```

**Function return value:** `8`.

**User note:** Raises the first number to the second. Large exponents/results are limited; complex-number results are unsupported.

#### 08. `absit(number)`

Absolute value.

```qwerty
sayit(absit(-7));
```

**Console output:**

```text
7
```

**Function return value:** `7`.

**User note:** Removes the sign of a number. It does not accept text or a boolean.

#### 09. `rootit(number)`

Non-negative square root.

```qwerty
sayit(rootit(25));
```

**Console output:**

```text
5.0
```

**Function return value:** `5.0`.

**User note:** The input must be non-negative. The result is a decimal; a negative input produces an error.

#### 10. `roundit(number, places=0)`

Round using ties-to-even; places -100..100.

```qwerty
sayit(roundit(3.14159, 2));
```

**Console output:**

```text
3.14
```

**Function return value:** `3.14`.

**User note:** The optional second argument is a positional integer from -100 to 100. Ties round to even: roundit(2.5) returns 2.0, roundit(3.5) returns 4.0. Floating-point values are not exact decimal arithmetic.

#### 11. `ceilit(number)`

Round toward positive infinity.

```qwerty
sayit(ceilit(2.1));
```

**Console output:**

```text
3
```

**Function return value:** `3`.

**User note:** Returns an integer rounded upward: ceilit(-2.8) returns -2.

#### 12. `floorit(number)`

Round toward negative infinity.

```qwerty
sayit(floorit(2.9));
```

**Console output:**

```text
2
```

**Function return value:** `2`.

**User note:** Returns an integer rounded downward: floorit(-2.1) returns -3.

#### 13. `minit(numbers)`

Smallest number; non-empty list.

```qwerty
sayit(minit([3, 1, 2]));
```

**Console output:**

```text
1
```

**Function return value:** `1`.

**User note:** Pass a single, non-empty list of numbers, not several separate numbers. Empty lists and nonnumeric elements raise errors.

#### 14. `maxit(numbers)`

Largest number; non-empty list.

```qwerty
sayit(maxit([3, 1, 2]));
```

**Console output:**

```text
3
```

**Function return value:** `3`.

**User note:** Pass one non-empty numeric list. It does not accept a list of text values.

#### 15. `sumit(numbers)`

Sum a numeric list; empty list returns zero.

```qwerty
sayit(sumit([1, 2, 3]));
```

**Console output:**

```text
6
```

**Function return value:** `6`.

**User note:** Pass a numeric list. sumit([]) returns 0. Boolean values are not treated as numbers.

#### 16. `avgit(numbers)`

Arithmetic mean; non-empty numeric list.

```qwerty
sayit(avgit([2, 4, 6]));
```

**Console output:**

```text
4.0
```

**Function return value:** `4.0`.

**User note:** Pass a non-empty numeric list. An empty list raises an error; a normal integer-list average is a decimal.

#### 17. `factorit(integer)`

Factorial of an integer from 0 to 500.

```qwerty
sayit(factorit(5));
```

**Console output:**

```text
120
```

**Function return value:** `120`.

**User note:** Requires an integer from 0 through 500 inclusive. factorit(0) is 1; negative values and decimals are rejected.

#### 18. `gcdit(a, b)`

Greatest common divisor of two integers.

```qwerty
sayit(gcdit(12, 18));
```

**Console output:**

```text
6
```

**Function return value:** `6`.

**User note:** Both inputs must be integers. The result is non-negative; gcdit(0, 0) is 0.

#### 19. `lcmit(a, b)`

Least common multiple of two integers.

```qwerty
sayit(lcmit(4, 6));
```

**Console output:**

```text
12
```

**Function return value:** `12`.

**User note:** Both inputs must be integers. The result is non-negative; an input of zero makes the result zero.

#### 20. `clampit(value, low, high)`

Limit a number to an inclusive interval.

```qwerty
sayit(clampit(12, 0, 10));
```

**Console output:**

```text
10
```

**Function return value:** `10`.

**User note:** The lower bound must not exceed the upper bound. All three inputs must be numbers.

### Logic

#### 21. `equalit(a, b)`

Structural equality; booleans are distinct from numbers.

```qwerty
sayit(equalit(3, 3.0));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Lists/maps are compared by their contents. Numbers 3 and 3.0 compare equal, but aye and 1 do not.

#### 22. `diffit(a, b)`

Structural inequality.

```qwerty
sayit(diffit(3, 4));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** The inverse of equalit(). This uses structural comparison for lists and maps.

#### 23. `greaterit(a, b)`

Compare numbers or text with >.

```qwerty
sayit(greaterit(3, 2));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Use two numbers or two text values. Text comparison is case-sensitive; mixing text and numbers raises an error.

#### 24. `lessit(a, b)`

Compare numbers or text with <.

```qwerty
sayit(lessit(3, 2));
```

**Console output:**

```text
nay
```

**Function return value:** `nay`.

**User note:** Use two numbers or two text values. To test a range, combine two comparisons with &&.

#### 25. `atleastit(a, b)`

Compare numbers or text with >=.

```qwerty
sayit(atleastit(3, 3));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Returns aye when the first value is greater than or equal to the second. Operands must be comparable numbers or text.

#### 26. `atmostit(a, b)`

Compare numbers or text with <=.

```qwerty
sayit(atmostit(4, 3));
```

**Console output:**

```text
nay
```

**Function return value:** `nay`.

**User note:** Returns aye when the first value is less than or equal to the second. Operands must be comparable numbers or text.

#### 27. `andit(a, b)`

Eager logical AND; returns a boolean.

```qwerty
sayit(andit(aye, nay));
```

**Console output:**

```text
nay
```

**Function return value:** `nay`.

**User note:** Both argument expressions run before this function is called. Use && instead when the second expression must be skipped if the first is false.

#### 28. `orit(a, b)`

Eager logical OR; returns a boolean.

```qwerty
sayit(orit(aye, nay));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Both argument expressions run before this function is called. Use || instead when the second expression must be skipped if the first is true.

#### 29. `notit(value)`

Logical negation of truthiness.

```qwerty
sayit(notit(nay));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Negates truthiness. void, nay, zero, empty text, empty lists, and empty maps are false; non-empty text such as "nay" is true.

### Text

#### 30. `concatit(...text)`

Concatenate text arguments without a separator.

```qwerty
sayit(concatit("Q", "WERTY"));
```

**Console output:**

```text
QWERTY
```

**Function return value:** `"QWERTY"`.

**User note:** Every argument must be text. Convert numbers with textit() first. No separator is inserted. Accepts zero through 256 arguments.

#### 31. `upperit(text)`

Text upper operation.

```qwerty
sayit(upperit("hello"));
```

**Console output:**

```text
HELLO
```

**Function return value:** `"HELLO"`.

**User note:** Returns new uppercase text; it does not update a variable automatically. Unicode case conversions can change text length.

#### 32. `lowerit(text)`

Text lower operation.

```qwerty
sayit(lowerit("HELLO"));
```

**Console output:**

```text
hello
```

**Function return value:** `"hello"`.

**User note:** Returns new lowercase text. Assign the result to retain it.

#### 33. `titleit(text)`

Text title operation.

```qwerty
sayit(titleit("hello world"));
```

**Console output:**

```text
Hello World
```

**Function return value:** `"Hello World"`.

**User note:** Returns title-cased text. Punctuation can affect word boundaries; it is not a human-name formatting system.

#### 34. `trimit(text)`

Text strip operation.

```qwerty
sayit(trimit("  hello  "));
```

**Console output:**

```text
hello
```

**Function return value:** `"hello"`.

**User note:** Removes leading and trailing whitespace, not spaces inside the text.

#### 35. `ltrimit(text)`

Text lstrip operation.

```qwerty
sayit(ltrimit("  hello  "));
```

**Console output:**

```text
hello  
```

**Function return value:** `"hello  "`.

**User note:** Removes only leading whitespace. The example retains two spaces after hello.

#### 36. `rtrimit(text)`

Text rstrip operation.

```qwerty
sayit(rtrimit("  hello  "));
```

**Console output:**

```text
  hello
```

**Function return value:** `"  hello"`.

**User note:** Removes only trailing whitespace. The example retains two spaces before hello.

#### 37. `splitit(text, separator=void)`

Split text; default separates whitespace.

```qwerty
sayit(splitit("a,b", ","));
```

**Console output:**

```text
["a", "b"]
```

**Function return value:** `["a", "b"]`.

**User note:** With no separator, splits on whitespace. An explicit separator must be non-empty text. The result is a list.

#### 38. `joinit(separator, text_list)`

Join a list of text values.

```qwerty
sayit(joinit("-", ["a", "b"]));
```

**Console output:**

```text
a-b
```

**Function return value:** `"a-b"`.

**User note:** The separator comes first. Every item in the second argument must already be text.

#### 39. `replaceit(text, old, new)`

Replace all matching substrings.

```qwerty
sayit(replaceit("abcabc", "a", "x"));
```

**Console output:**

```text
xbcxbc
```

**Function return value:** `"xbcxbc"`.

**User note:** Replaces all occurrences, not just the first. All three arguments must be text; the result has a size limit.

#### 40. `findit(text, target)`

First substring index, or -1 when missing.

```qwerty
sayit(findit("hello", "ll"));
```

**Console output:**

```text
2
```

**Function return value:** `2`.

**User note:** Indices start at zero. A missing substring returns -1; it does not raise an error.

#### 41. `startsit(text, prefix)`

Test a text prefix.

```qwerty
sayit(startsit("hello", "he"));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Prefix testing is case-sensitive. An empty prefix matches any text.

#### 42. `endsit(text, suffix)`

Test a text suffix.

```qwerty
sayit(endsit("hello", "lo"));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Suffix testing is case-sensitive. An empty suffix matches any text.

#### 43. `countit(sequence, target)`

Count non-overlapping substrings or equal list items.

```qwerty
sayit(countit("banana", "an"));
```

**Console output:**

```text
2
```

**Function return value:** `2`.

**User note:** For text, counts non-overlapping substrings. For a list, counts structurally equal items.

#### 44. `repeatit(text, count)`

Repeat text a non-negative integer number of times.

```qwerty
sayit(repeatit("ha", 3));
```

**Console output:**

```text
hahaha
```

**Function return value:** `"hahaha"`.

**User note:** The count must be a non-negative integer. A count of zero returns empty text; oversized results are rejected.

#### 45. `sliceit(sequence, start, stop)`

Copy a slice; stop is excluded, bounds may be negative.

```qwerty
sayit(sliceit("hello", 1, 4));
```

**Console output:**

```text
ell
```

**Function return value:** `"ell"`.

**User note:** Works on text or a list. Start is included, stop is excluded; negative bounds are allowed. There is no step argument.

#### 46. `charit(codepoint)`

Unicode scalar value to a character.

```qwerty
sayit(charit(65));
```

**Console output:**

```text
A
```

**Function return value:** `"A"`.

**User note:** Accepts one valid Unicode scalar integer from 0 to 0x10FFFF, excluding surrogate values. Write numbers in decimal in QWERTY source; hexadecimal literals are unsupported.

#### 47. `codeit(character)`

A single character to its Unicode codepoint.

```qwerty
sayit(codeit("A"));
```

**Console output:**

```text
65
```

**Function return value:** `65`.

**User note:** Requires exactly one Unicode code point as text. Some visible emoji consist of multiple code points and are rejected.

#### 48. `alphait(text)`

Whether non-empty text contains only Unicode letters.

```qwerty
sayit(alphait("hello"));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Returns aye only for non-empty text made entirely of Unicode letters. Spaces make it nay.

#### 49. `digitit(text)`

Whether non-empty text contains only Unicode digits.

```qwerty
sayit(digitit("123"));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Recognizes Unicode digit characters, not just ASCII 0-9. A sign or decimal point makes it nay; aye does not guarantee intit() accepts every Unicode digit string.

### Lists

#### 50. `listit(...values)`

Build a new list from positional values.

```qwerty
sayit(listit(1, 2, 3));
```

**Console output:**

```text
[1, 2, 3]
```

**Function return value:** `[1, 2, 3]`.

**User note:** Builds a list from zero through 256 arguments. Mixed value types are allowed. You can also use [1, 2, 3] list syntax.

#### 51. `sizeit(collection)`

Length of text, a list, or a map.

```qwerty
sayit(sizeit([1, 2, 3]));
```

**Console output:**

```text
3
```

**Function return value:** `3`.

**User note:** Counts items in a list, keys in a map, or Unicode code points in text. This is not a visual character/grapheme counter.

#### 52. `pushit(list, value)`

Return a new list with value appended.

```qwerty
sayit(pushit([1, 2], 3));
```

**Console output:**

```text
[1, 2, 3]
```

**Function return value:** `[1, 2, 3]`.

**User note:** Returns a NEW list. Use items = pushit(items, value); the original list is not modified.

#### 53. `firstit(sequence)`

First item; error for an empty sequence.

```qwerty
sayit(firstit([7, 8]));
```

**Console output:**

```text
7
```

**Function return value:** `7`.

**User note:** Works with a list or text. An empty sequence raises an IndexError.

#### 54. `lastit(sequence)`

Last item; error for an empty sequence.

```qwerty
sayit(lastit([7, 8]));
```

**Console output:**

```text
8
```

**Function return value:** `8`.

**User note:** Works with a list or text. An empty sequence raises an IndexError.

#### 55. `pickit(sequence, index)`

Read a zero-based index; negative indices count from the end.

```qwerty
sayit(pickit([4, 5, 6], 1));
```

**Console output:**

```text
5
```

**Function return value:** `5`.

**User note:** Works with a list or text. Index 0 is the first item, -1 is the last. An out-of-range index raises an error.

#### 56. `putit(list, index, value)`

Return a list with one existing index replaced.

```qwerty
sayit(putit([1, 2], 0, 9));
```

**Console output:**

```text
[9, 2]
```

**Function return value:** `[9, 2]`.

**User note:** Replaces an existing list position and returns a NEW list. It does not insert or extend; assign the result back.

#### 57. `popit(list)`

Return a list without its last item; does not return that item.

```qwerty
sayit(popit([1, 2, 3]));
```

**Console output:**

```text
[1, 2]
```

**Function return value:** `[1, 2]`.

**User note:** Returns a NEW list with its last item removed, NOT the removed item. Use lastit() to read that item first. Empty lists raise an error.

#### 58. `removeit(list, value)`

Return a list with its first matching value removed.

```qwerty
sayit(removeit([1, 2, 1], 1));
```

**Console output:**

```text
[2, 1]
```

**Function return value:** `[2, 1]`.

**User note:** Removes only the first equal item and returns a NEW list. A missing value raises an error; assign the result back.

#### 59. `sortit(list, descending=nay)`

Return a sorted numeric or text list.

```qwerty
sayit(sortit([3, 1, 2]));
```

**Console output:**

```text
[1, 2, 3]
```

**Function return value:** `[1, 2, 3]`.

**User note:** Accepts an all-number or all-text list. The optional positional second argument must be aye/nay: sortit(items, aye) sorts descending. Mixed text/number lists are rejected.

#### 60. `reverseit(sequence)`

Return reversed text or a reversed list.

```qwerty
sayit(reverseit([1, 2, 3]));
```

**Console output:**

```text
[3, 2, 1]
```

**Function return value:** `[3, 2, 1]`.

**User note:** Returns reversed text or a NEW reversed list; the input is unchanged.

#### 61. `uniqueit(list)`

Remove duplicates, preserving first occurrence order.

```qwerty
sayit(uniqueit([1, 2, 1, 3]));
```

**Console output:**

```text
[1, 2, 3]
```

**Function return value:** `[1, 2, 3]`.

**User note:** Preserves the first occurrence order and compares nested values structurally. Large nested inputs can hit the execution budget.

#### 62. `spanit(stop) or spanit(start, stop, step=1)`

Integer range as a list; stop excluded; step cannot be zero.

```qwerty
sayit(spanit(1, 6, 2));
```

**Console output:**

```text
[1, 3, 5]
```

**Function return value:** `[1, 3, 5]`.

**User note:** Use spanit(stop), spanit(start, stop), or spanit(start, stop, step). All arguments are integers. Stop is excluded, the step cannot be zero, and the result is a bounded list, not a lazy iterator.

#### 63. `mergeit(list_a, list_b)`

Concatenate two lists into a new list.

```qwerty
sayit(mergeit([1, 2], [3]));
```

**Console output:**

```text
[1, 2, 3]
```

**Function return value:** `[1, 2, 3]`.

**User note:** Both inputs must be lists. Duplicates are preserved; combine with uniqueit() to remove them.

#### 64. `emptyit(collection)`

Whether text, a list, or a map has zero items.

```qwerty
sayit(emptyit([]));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Works with text, lists, and maps. void is not an empty collection and is rejected.

### Maps

#### 65. `mapit(keys, values)`

Build a map; duplicate keys use the last value.

```qwerty
sayit(mapit(["a", "b"], [1, 2]));
```

**Console output:**

```text
{"a": 1, "b": 2}
```

**Function return value:** `{"a": 1, "b": 2}`.

**User note:** Keys must be text and the two lists must have equal lengths. Duplicate keys keep the last supplied value. Use mapit([], []) for an empty map; map literals are unsupported.

#### 66. `getit(map, key, default=void)`

Read a key, returning default if absent.

```qwerty
sayit(getit(mapit(["a"], [1]), "a"));
```

**Console output:**

```text
1
```

**Function return value:** `1`.

**User note:** A missing key returns the optional positional default, or void if no default is supplied. It does not create a new key.

#### 67. `setit(map, key, value)`

Return a map with a key inserted or replaced.

```qwerty
sayit(setit(mapit([], []), "a", 1));
```

**Console output:**

```text
{"a": 1}
```

**Function return value:** `{"a": 1}`.

**User note:** Returns a NEW map with the text key inserted or replaced. Use profile = setit(profile, "age", 26); to retain it.

#### 68. `keysit(map)`

Keys in insertion order.

```qwerty
sayit(keysit(mapit(["a", "b"], [1, 2])));
```

**Console output:**

```text
["a", "b"]
```

**Function return value:** `["a", "b"]`.

**User note:** Returns a list of text keys in insertion order, not sorted order.

#### 69. `valuesit(map)`

Values in insertion order.

```qwerty
sayit(valuesit(mapit(["a", "b"], [1, 2])));
```

**Console output:**

```text
[1, 2]
```

**Function return value:** `[1, 2]`.

**User note:** Returns a list of values in insertion order; its positions correspond to keysit() on the same map.

#### 70. `hasit(collection, value)`

Test a map key, substring, or equal list item.

```qwerty
sayit(hasit(mapit(["a"], [1]), "a"));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** For maps, checks keys, not values. For text, checks a substring; for lists, checks an equal item.

### Types

#### 71. `textit(value)`

Convert to QWERTY display text.

```qwerty
sayit(textit(aye));
```

**Console output:**

```text
aye
```

**Function return value:** `"aye"`.

**User note:** Uses QWERTY spellings: aye, nay, and void. Collection elements are formatted with quotes for text. This is display formatting, not a JSON serializer.

#### 72. `intit(value)`

Numeric text or number to an integer; decimals truncate toward zero.

```qwerty
sayit(intit("42"));
```

**Console output:**

```text
42
```

**Function return value:** `42`.

**User note:** Numeric values truncate toward zero: intit(3.9) is 3. Integer text such as "42" works, but decimal text "3.5" does not; use intit(floatit("3.5")). Booleans are rejected.

#### 73. `floatit(value)`

Numeric text or number to a finite decimal.

```qwerty
sayit(floatit("3.5"));
```

**Console output:**

```text
3.5
```

**Function return value:** `3.5`.

**User note:** Accepts a number or numeric text, not a boolean. Invalid text and non-finite results raise errors.

#### 74. `boolit(value)`

Truthiness conversion; non-empty text including 'nay' is true.

```qwerty
sayit(boolit(0));
```

**Console output:**

```text
nay
```

**Function return value:** `nay`.

**User note:** This tests truthiness; it does not parse boolean words. boolit("nay") is aye because the string is non-empty.

#### 75. `typeit(value)`

Return void/boolean/integer/decimal/text/list/map.

```qwerty
sayit(typeit("hello"));
```

**Console output:**

```text
text
```

**Function return value:** `"text"`.

**User note:** Returns one of the text values void, boolean, integer, decimal, text, list, or map.

#### 76. `isnumit(value)`

Test for integer or decimal; excludes booleans.

```qwerty
sayit(isnumit(3.5));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Returns aye only for numeric values, not numeric text or booleans. isnumit("42") is nay.

#### 77. `istextit(value)`

Test for a text value.

```qwerty
sayit(istextit("hello"));
```

**Console output:**

```text
aye
```

**Function return value:** `aye`.

**User note:** Returns aye for any text value, including empty text. It does not convert a value.

### I/O

#### 78. `sayit(...values)`

Print values separated by spaces and end with a newline; return void.

```qwerty
sayit("hello");
```

**Console output:**

```text
hello
```

**Function return value:** `void`.

**User note:** Prints arguments separated by spaces and adds a newline. Its return value is void. Do not wrap sayit() inside another sayit() unless you deliberately want to print void. Zero arguments prints a blank line.

#### 79. `askit(prompt="")`

Write a prompt and consume one input line as text.

**Program input before running:** `Ada`

```qwerty
sayit(askit("Name: "));
```

**Console output:**

```text
Name: Ada
```

**Function return value:** `"Ada"`.

**User note:** In the browser, fill Program input BEFORE clicking Run: one line for each call. It returns text and writes the prompt without a newline. The example needs the input Ada. No popup is displayed; convert numeric input explicitly.

#### 80. `assertit(condition, message="Assertion failed.")`

Raise an assertion error if condition is false; otherwise return void.

```qwerty
assertit(aye, "failed");
```

**Console output:** none on success. This is expected.

**Function return value:** `void`.

**User note:** Success deliberately prints nothing and returns void. A false condition stops execution with an AssertionError and the supplied message. Use sayit("Passed"); afterward for a visible success message.

## 9. Verification and maintenance

Read `TEST_REPORT.md` for the exact checks executed in this package and their limitations. The original project's earlier report is preserved as `TEST_REPORT_LOCAL_ORIGINAL.md`; it is not a verification report for this new deployment.

After changing any Python engine code, built-in metadata, reference notes, or guide templates, regenerate the committed hosted assets:

```powershell
py -3 scripts/build_static.py
py -3 -m unittest discover -s tests -v
```

The build script uses Python's standard library only. It regenerates the browser compiler archive, function catalog, Markdown guide, HTML reference, and reference-example data. Vercel deliberately skips a build because these files are already committed. Forgetting to regenerate them would deploy the previous embedded engine.

Before publishing an update, preview `public/` over HTTP, run the live smoke checks in section 5, and then commit the updated `public/` files along with your source. Keep runtime versions pinned; changing the Pyodide URL requires new browser testing. Do not silently replace the browser architecture with an unprotected public Python execution API.

The original CLI is still available:

```powershell
py -3 -m qwerty run examples/demo.qw
py -3 -m qwerty check examples/demo.qw
py -3 -m qwerty compile examples/demo.qw -o demo.qbc
py -3 -m qwerty run demo.qbc
```

No general claim of production security, exhaustive language correctness, or cross-browser compatibility is made. See the package's current test report before describing it as tested on a particular platform.

## 10. Official deployment references

Provider guidance was checked on 18 September 2026. Dashboard wording, service limits, and versions can change. These references describe the external platforms; the language behavior is defined by this project's source and tests.

[1] Pyodide usage and deployment: `https://pyodide.org/en/stable/usage/index.html` and `https://pyodide.org/en/stable/usage/downloading-and-deploying.html`.

[2] Pyodide module workers and custom Python packages: `https://pyodide.org/en/stable/usage/webworker.html` and `https://pyodide.org/en/stable/usage/loading-custom-python-code.html`.

[3] Vercel Drop workflow and limitations: `https://vercel.com/docs/drop`.

[4] Vercel Git deployments: `https://vercel.com/docs/git`.

[5] Vercel static build/output settings: `https://vercel.com/docs/builds/configure-a-build` and `https://vercel.com/docs/project-configuration/vercel-json`.

[6] Vercel Hobby usage policy: `https://vercel.com/docs/plans/hobby`.
