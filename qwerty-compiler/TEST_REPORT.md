# QWERTY v1 Verification Report

Verification date: 2026-09-18.

## Core test result

The final test run completed on **CPython 3.13.5, Linux**:

```text
python -m unittest discover -s tests -v

Ran 302 tests in 5.550s

OK
```

The full output is in `verification/unittest.log`. The suite includes an executed
example and a rejected argument count for each of the 80 built-ins. It also covers
expression precedence, short-circuit versus eager logic, branch/loop control,
lexical scope, recursion and mutual recursion, global initialization, immutable
collection updates, input/output, diagnostics, execution limits, instruction-file
round trips and rejection, command-line flows, local HTTP checks, and worker runs.

Randomized cases include 100 arithmetic expressions and 300 malformed/small source
inputs. These checks are useful regression tests, not exhaustive verification,
a security audit, or a proof that every possible program is handled correctly.

Python source compilation succeeded with `python -m compileall -q qwerty tests`.
The browser JavaScript passed `node --check web/app.js` in Node 22.16.0. Node is
**not** needed to run this project.

## Browser workflow verification

Ten checks passed using Chromium and Playwright in the verification environment:
welcome program execution; instruction-tab content; recursion; supplied input;
compile-only checking versus a runtime failure; literal HTML-like output handling;
function search; source download; a 390-pixel responsive viewport; and absence of
uncaught JavaScript errors. The recorded checks are in
`verification/browser-checks.json`.

Environment qualification: Chromium's administrator policy blocked direct
navigation to loopback URLs in this environment. The UI checks therefore loaded
the same HTML/CSS/JavaScript into an offline page and bridged its fetch calls through
Python to the **actual local HTTP server**. This verified client behavior with the
real backend, but is not a claim that direct browser navigation was tested here.
The HTTP server was also exercised independently by the core test suite, including
host/origin/token rejection. On a normal local installation, open the address
printed by `python -m qwerty web`.

`docs/studio-preview.png` is a screenshot of the real UI rendering a successfully
executed welcome program in that harness, not a design mockup.

## Untested / out of scope

Windows and macOS execution were not available for this verification. The Windows
batch launcher is included but was not executed on Windows. Python 3.11+ is the
compatibility target; only Python 3.13.5 was executed here. Older/newer interpreter
versions should be tested in the target environment before making compatibility
claims beyond that result.

No public deployment, multi-user load test, independent security audit, exhaustive
fuzzing, native-code backend, or comprehensive cross-browser test was performed.
Read SECURITY.md before considering deployment beyond your own machine.
