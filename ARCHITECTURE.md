# Compiler architecture and extension guide

## Pipeline

```text
.qw source
    |
    v
Lexer -> tokens with line/column
    |
    v
Parser -> abstract syntax tree
    |
    v
Semantic compiler -> name binding, arity, scope, control-flow validation
    |
    v
QWERTY instruction stream -> optional .qbc JSON serialization
    |
    v
Validated stack VM -> program output / structured diagnostics
```

The parser is handwritten recursive descent for statements and precedence
climbing for expressions. It does not use Python parsing, regex substitution as
a compiler, Python `eval`, or Python `exec`.

## AST and lexical binding

`Node` stores a kind, originating token, value, and child nodes. The compiler
pre-registers top-level function signatures and global variable slots. Each
function is compiled separately using a lexical scope stack.

Local names resolve to frame slots at compile time. Direct module variables have
stable main-frame slots. Functions use separate global-load/store instructions
when resolving a module variable rather than a local. Block-local names get fresh
slots even when they shadow outer names. Values in a reused loop-body slot are
initialized again when its declaration executes.

Top-level functions are hoisted, but top-level variable initialization is not.
Unknown names and invalid function arities are rejected before execution. Value
and type errors that depend on execution are checked by the VM/standard library.

## Instruction format

The instruction record contains a numeric opcode, operand, and source line/column.
`bytecode.py` assigns the opcode numbers. The principal operations are:

| Family | Operations |
|---|---|
| Values | CONST, LOAD_LOCAL, STORE_LOCAL, LOAD_GLOBAL, STORE_GLOBAL |
| Stack / expressions | POP, BUILD_LIST, INDEX, UNARY, BINARY, BOOL |
| Control flow | JUMP, JUMP_FALSE, JUMP_FALSE_KEEP, JUMP_TRUE_KEEP |
| Functions | CALL, RETURN |
| Iteration | ITER, ITER_NEXT |
| Completion | HALT |

The `.qbc` file is a versioned JSON representation of this instruction program.
It is an executable QWERTY intermediate representation, not a native executable
and not a CPython `.pyc` file. Human-readable disassembly names the opcodes.

For example, `sayit(addit(2,3));` becomes constant loads, a two-argument `addit`
call, a one-argument `sayit` call, a discard of `sayit`'s `void` result, and HALT.

Before executing a loaded instruction file, the loader validates schema, limits,
constants, operand shapes, slots, jumps, functions, call arity, source positions,
and reachable stack heights. It rejects inconsistent branch stack heights and
paths that fall out of a chunk. This is structural validation, not a proof of all
program properties. Values and hidden iterator types still need runtime checks.

## Virtual machine

Each frame holds a function chunk, instruction pointer, local slots, and operand
stack. Calling a crafted function pushes a VM frame rather than recursively
calling the Python evaluator. Returning transfers one value to the caller's
operand stack. An explicit call-depth budget limits recursion.

Each operation is dispatched through a fixed instruction handler. Built-ins are
resolved only through the explicit registry in `builtins.py`. Python attributes,
modules, and host functions are not exposed by name lookup.

`Context` owns all per-run input, output, clocks, and counters. The public
`execute()` API creates a fresh program context; one execution does not inherit
variables from another execution. `QwertyError` adds source excerpts and a VM
function trace. Python implementation exceptions expected from numeric/value
operations are converted to language diagnostics.

Collection updates are immutable. This reduces accidental aliasing surprises and
prevents source programs from constructing cyclic values through list/map mutation.
Value guards use graph-aware traversal; output rendering is independently bounded.

## Browser editor

The browser client is plain HTML/CSS/JavaScript and makes local JSON requests.
The standard-library server serves only an explicit set of static assets and two
API routes. Host/origin checks and a per-server token restrict execution requests.

`POST /api/execute` accepts `source`, `input`, and an `action` of `run` or `check`.
Each request uses a fresh multiprocessing worker. The parent applies a worker
wall-clock limit. The VM adds cooperative instruction/time/value/output budgets.
The UI prints output and diagnostics using text nodes, not executable HTML.

The frontend is not a static-only compiler and cannot run by uploading only its
web folder to static hosting. A production execution service is a separate project;
see SECURITY.md.

## Add a built-in

1. Implement a Python callable with `Context` as its first argument. Accept only
   QWERTY values, validate inputs with the helpers in `values.py`, and return only
   supported values. Check size before allocating expanded strings/collections.
2. Add a `register(...)` entry in `builtins.py`: custom name, signature, category,
   minimum/maximum argument counts, description, runnable example, expected value,
   and implementation. Choose a language-facing name ending in `it`.
3. Add boundary/type-error tests. The standard tests automatically add an example
   and an invalid-arity test for every registered function. Update the exact-count
   assertion, README table, BUILTINS.md, and any UI/demo function counts.
4. Run `python -m unittest discover -s tests -v` and inspect the new function in
   `python -m qwerty functions`.

Do not register a generic evaluator, module importer, filesystem handle, object
attribute accessor, subprocess launcher, or unrestricted callback as a shortcut.

## Add syntax

Update the lexer only when new tokens are needed. Add the parser rule and AST
shape, add compiler lowering and semantic validation, and add a VM operation only
when existing instructions cannot express the feature. New instructions must be
recognized by the serialization validator and stack-effect analysis. Tests should
cover both valid programs and rejected inputs. Changes to persisted instruction
semantics require an explicit format-version policy.

## Design references

These primary references explain the architectural concepts; this implementation
is an original Python project, not a copy of their C or Java implementation.

- Robert Nystrom, *Crafting Interpreters*, "Chunks of Bytecode":
  https://craftinginterpreters.com/chunks-of-bytecode.html
- Robert Nystrom, *Crafting Interpreters*, "A Virtual Machine":
  https://craftinginterpreters.com/a-virtual-machine.html
- Python documentation, built-in `eval` and `exec` security warnings:
  https://docs.python.org/3/library/functions.html
- Python documentation, `http.server` production limitations:
  https://docs.python.org/3/library/http.server.html
