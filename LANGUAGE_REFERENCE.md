# QWERTY v1: Language Reference

## Program model

A program is UTF-8 QWERTY source, conventionally in a `.qw` file. Source is compiled
in full before any statement executes. The generated instructions execute on the
QWERTY stack VM implemented in Python. Line endings are normalized to LF.

The language is dynamically typed. Variables can later hold a value of a different
type, but operations validate the types they need. There is no implicit numeric
conversion from text or booleans.

## Tokens and literals

Identifiers use `[A-Za-z_][A-Za-z0-9_]*`, are case-sensitive, and cannot begin with
`__`. Keywords are:

```text
keep craft give when otherwise whilst each over stop skip aye nay void
```

Literals include integers (`12`), decimal/exponent numbers (`3.5`, `1.2e3`), text
(`"hello"` or `'hello'`), booleans (`aye`, `nay`), and null (`void`). Negative
numbers use unary minus. Number literals must begin with a digit; use `0.5`, not
`.5`. Complex numbers, NaN, and infinities are not supported.

Text supports `\n`, `\r`, `\t`, `\\`, `\"`, `\'`, and `\uXXXX`. A Unicode escape
must be a valid, non-surrogate scalar. Literal Unicode characters are supported
in strings, but identifiers remain ASCII. A string cannot span physical lines;
use `\n` to embed a newline.

`#` begins a line comment. `/* ... */` is a non-nesting block comment. `//` is the
floor-division operator, not a line comment.

## Statements and blocks

```qwerty
keep score = 10;                 # declaration
score = addit(score, 5);         # reassignment
sayit(score);                   # expression statement
{ keep temporary = "local"; }    # lexical block
```

Simple statements require a semicolon. Blocks require `{` and `}` and do not
require a following semicolon. Indentation and line breaks do not define blocks.
There are no compound assignments (`+=`), increment operators, or indexed
assignments. Use ordinary assignment or a collection-update helper.

### Conditional execution

```qwerty
when score >= 90 {
    sayit("A");
} otherwise when score >= 75 {
    sayit("B");
} otherwise {
    sayit("C");
}
```

Parentheses around a condition are optional. Conditions use truthiness: `void`,
`nay`, zero, empty text, an empty list, and an empty map are false. Other language
values are true. Consequently, `boolit("nay")` is `aye`: non-empty text is true.

### Loops

```qwerty
keep i = 0;
whilst i < 5 {
    i = addit(i, 1);
    when i == 2 { skip; }
    when i == 4 { stop; }
    sayit(i);
}

each value over spanit(1, 4) {
    sayit(value);
}
```

`stop` exits the innermost loop. `skip` starts its next iteration. Both require a
semicolon and must appear inside a loop. A for-each iterable is evaluated once.
Text iterates over characters, lists over values, and maps over keys in insertion
order. For-each loop variables are local to their loop. `spanit()` excludes its
stop bound and returns a bounded list, not a lazy generator.

## Expressions and precedence

From lowest to highest precedence:

| Operators | Meaning | Associativity |
|---|---|---|
| `||` | Short-circuit logical OR | Left |
| `&&` | Short-circuit logical AND | Left |
| `==`, `!=` | Equality / inequality | Left |
| `<`, `<=`, `>`, `>=` | Ordering | Left |
| `+`, `-` | Numeric addition / subtraction | Left |
| `*`, `/`, `//`, `%` | Numeric multiply / division / floor division / remainder | Left |
| unary `+`, `-`, `!` | Numeric identity / negation / logical NOT | Prefix |
| `**` | Exponentiation | Right |
| `name(...)`, `value[index]` | Named call / indexing | Postfix |

`2 + 3 * 4` is 14, `2 ** 3 ** 2` is 512, `-2 ** 2` is -4, and `2 ** -2` is 0.25.
Use explicit `&&` for chained comparisons: `0 < x && x < 10`. Python-style chained
comparisons are not a language feature; `0 < x < 10` is not interpreted as a range
test.

Arithmetic operators require numbers, not strings or lists. Use `concatit()` for
text concatenation and `mergeit()` for lists. Booleans are not accepted as numbers.
`/` returns a decimal value. `//` floors toward negative infinity. Decimals use
Python floating-point values and are not exact decimal arithmetic.

Ordering requires two numbers or two text values. Equality compares list/map
contents recursively; integer and decimal numbers compare by numeric value, but
booleans remain distinct: `equalit(1, 1.0)` is `aye`, while `equalit(aye, 1)` is `nay`.

`&&` and `||` skip an unnecessary right-hand expression and return a boolean.
`andit()` and `orit()` are ordinary eager functions: both argument expressions
are evaluated before the function is called.

## Functions and variable scope

```qwerty
keep base = 10;

craft increase(amount) {
    keep result = addit(base, amount);
    give result;
}

sayit(increase(5));
```

Crafted functions must be defined at the top level. They can be called before
their definition appears, and recursion/mutual recursion are supported. Arguments
are positional and evaluated left-to-right. User-defined default parameters and
variadic parameters are not supported. A bare `give;` or reaching the end of a
function returns `void`.

A `keep` declaration defines a name in its current lexical scope. Duplicate names
in the same scope are errors. Nested blocks may shadow outer variables. A crafted
function's parameters and outer body share one scope. Built-in and crafted function
names cannot be reused for variables or parameters.

Functions see their own lexical locals plus direct top-level variables. They do
not see another caller's local variables: this is lexical, not dynamic, scope.
Functions may read or reassign a declared top-level variable, but its declaration
must have executed first. Top-level variables are pre-indexed so the compiler can
resolve a global mentioned inside a function; reading/writing an as-yet
uninitialized global is then a runtime error.

There are no nested functions, closures, function references, callbacks, anonymous
functions, object attributes, classes, methods, or imports in v1.

## Collections and conversion

```qwerty
keep items = [10, 20, 30];
sayit(items[0], items[-1]);
items = putit(items, 1, 99);
items = pushit(items, 40);

keep person = mapit(["name", "age"], ["Ada", 25]);
person = setit(person, "age", 26);
sayit(getit(person, "name"));
```

Lists may hold mixed types and nested lists/maps. Indexing is zero-based; negative
indices count from the end. Indexing only supports text and lists. Read map keys
with `getit()`. Map keys are text only; duplicate keys in `mapit()` use the last
supplied value. A missing `getit()` key returns its explicit default, or `void`.

Collections are language-level immutable values. `pushit`, `putit`, `popit`,
`removeit`, `sortit`, `reverseit`, `uniqueit`, `mergeit`, and `setit` return a new
result, leaving the input unchanged. In particular, `popit([1,2,3])` returns `[1,2]`,
not the removed item. `lastit()` reads the last item. Copies may share nested
immutable values internally; the language offers no mutating back door.

`intit()` converts numeric text or truncates a decimal toward zero. `floatit()`
converts numeric text or a number to a finite decimal. `textit()` uses QWERTY
spellings such as `aye` and `void`. `typeit()` returns one of `void`, `boolean`,
`integer`, `decimal`, `text`, `list`, or `map`.

## Input, output, and diagnostics

`sayit()` separates arguments with spaces, adds a newline, and returns `void`.
`askit()` writes its optional prompt and returns one line of text. Use `intit()` or
`floatit()` for numeric input. In the local editor, inputs are supplied in advance;
in the terminal, input is interactive unless `--input` is provided.

`assertit(condition, message)` raises a diagnostic when the condition is false.
It is not a user-defined exception-handling system. Syntax, compile, and runtime
errors halt the current operation and preserve appropriate source locations.

Programs can exhaust configurable execution budgets. See SECURITY.md for defaults
and why they are not a hostile-code sandbox.

## Compact grammar

```ebnf
program       = { statement } ;
statement     = "keep" NAME "=" expression ";"
              | NAME "=" expression ";"
              | "craft" NAME "(" [ parameters ] ")" block
              | when_statement
              | "whilst" expression block
              | "each" NAME "over" expression block
              | "give" [ expression ] ";"
              | ("stop" | "skip") ";"
              | block
              | expression ";" ;
when_statement = "when" expression block
                 [ "otherwise" (block | when_statement) ] ;
block         = "{" { statement } "}" ;
parameters    = NAME { "," NAME } ;
arguments     = expression { "," expression } ;
primary       = NUMBER | STRING | "aye" | "nay" | "void" | NAME
              | "(" expression ")"
              | "[" [ expression { "," expression } [ "," ] ] "]" ;
```

The expression precedence table supplies the operator grammar. Semantic rules
further restrict function declarations to top level, calls to named functions,
and return/loop control to their valid contexts. The grammar is descriptive; the
parser and tests are the executable specification.
