# Security boundary and limitations

## Intended use

This release is a local learning/development project. It is **not** a production
multi-tenant execution service and has not had an independent security audit.
Do not execute hostile programs on a machine containing sensitive data. Do not
publish or port-forward the included local server.

The absence of `eval()` is useful but does not by itself establish sandbox safety.
A custom runtime can still have implementation bugs, CPU denial of service,
excessive allocation, and platform-dependent failure modes.

## Implemented controls

QWERTY programs have no imports, attribute access, file I/O, network I/O, subprocess
functions, or route to arbitrary Python name lookup. Function calls go through an
explicit registry or compiler-defined function table. Collection updates return
new values rather than permitting cyclic mutation. The loaded `.qbc` format uses
JSON, not executable Python deserialization, and performs structural/stack checks.

The browser server binds only to loopback. It serves only fixed asset paths,
checks Host and Origin, requires a per-server execution token, does not enable
CORS, and supplies a restrictive Content Security Policy. The UI treats source,
output, and errors as text rather than HTML.

Every browser check/run request has a fresh worker process. The parent terminates
a worker that exceeds 6 seconds. On POSIX, the worker attempts a 256 MiB address-space
cap. That extra limit is platform-dependent/best-effort and may not be available.
**Windows does not get a hard OS-level memory cap from this implementation.**

## Default interpreter limits

| Resource | Default |
|---|---:|
| Source characters | 100,000 |
| Tokens | 30,000 |
| Total instructions in a compiled program | 60,000 |
| Executed VM instructions | 200,000 |
| VM execution time | 3 seconds, cooperative checks |
| Browser worker wall-clock duration | 6 seconds, parent process enforcement |
| Nested crafted-function calls | 100 |
| Items in one list or map | 10,000 |
| Characters in one text value | 100,000 |
| Output characters per run | 200,000 |
| Integer magnitude | 4,096 bits |
| Nested value depth | 50 |
| Value-graph traversal nodes | 50,000 |
| Positional arguments / parameters | 256 |
| Compiled instruction file input | 8 MB |

Some functions impose additional limits: factorial inputs 0..500, exponent
magnitude at most 10,000, and round precision -100..100. These limits are a small
language's documented operating envelope, not arbitrary-precision numerical support.

VM time/step checks occur at instruction boundaries and in selected helpers.
A single Python-native library operation can run between checks. The CLI and
in-process embedding API do not have a separate parent process enforcing their
time limit. Interactive terminal input can wait indefinitely and is intentionally
excluded from the timer. Per-value caps are not an aggregate heap-memory quota.
Many retained medium-sized values can still consume substantial memory.

The browser worker wall-clock timeout is stronger than the VM's cooperative time
checks but still does not replace OS isolation, a resource-restricted account, or
a hardened hosting architecture. The HTTP server is single-user development
infrastructure, not an authentication/rate-limiting system.

## Before public deployment

Design a separate, isolated execution service with enforced CPU/memory/process/
wall-clock quotas, an unprivileged runtime, a read-only/minimal filesystem, no
network egress unless explicitly required, concurrency limits, output caps,
request-size limits, authentication where appropriate, rate limiting, dependency
maintenance, and a threat-model-driven security review. Keep execution workers
separate from application credentials and other users' data.

Do not merely change `127.0.0.1` to `0.0.0.0`, add a public tunnel, or upload the
local-server code to a web host and treat it as production-ready.

The Python documentation explicitly warns that `http.server` is not recommended
for production and implements only basic security checks:
https://docs.python.org/3/library/http.server.html

The Python documentation also warns against passing untrusted user input to
`eval`/`exec`. This project avoids those execution paths:
https://docs.python.org/3/library/functions.html

## Other cautions

The `.qbc` format embeds its source and is not obfuscation or encryption. Do not
put secrets in sample programs. The browser saves source drafts in local storage
when available; clear that storage or use a separate browser profile on shared
machines. No telemetry, analytics, external JavaScript, or external fonts are
included in the editor.
