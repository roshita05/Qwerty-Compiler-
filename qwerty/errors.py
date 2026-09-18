"""Source-aware, user-facing QWERTY diagnostics."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    line: int = 1
    column: int = 1


class QwertyError(Exception):
    def __init__(self, kind: str, message: str, location: Location | None = None,
                 *, code: str = "Q0000", hint: str = "") -> None:
        super().__init__(message)
        self.kind, self.message, self.code, self.hint = kind, message, code, hint
        self.location = location or Location()
        self.filename, self.source = "<source>", ""
        self.trace: list[str] = []

    def attach(self, source: str, filename: str) -> QwertyError:
        self.source, self.filename = source, filename
        return self

    def as_dict(self) -> dict:
        return {"kind": self.kind, "code": self.code, "message": self.message,
                "line": self.location.line, "column": self.location.column,
                "hint": self.hint, "trace": self.trace, "formatted": str(self)}

    def __str__(self) -> str:
        line, column = self.location.line, self.location.column
        parts = [f"{self.kind} [{self.code}] at {self.filename}:{line}:{column}", self.message]
        lines = self.source.splitlines()
        if 1 <= line <= len(lines):
            raw = lines[line - 1]
            # Keep a useful excerpt even for programs with extremely long lines.
            start = max(0, column - 1 - 65)
            snippet = raw[start:start + 140].expandtabs(4)
            offset = len(raw[start:column - 1].expandtabs(4))
            prefix = "..." if start else ""
            parts.extend([f"  {line} | {prefix}{snippet}",
                          " " * (len(str(line)) + 5 + len(prefix) + offset) + "^"])
        if self.hint:
            parts.append(f"Hint: {self.hint}")
        if self.trace:
            parts.append("QWERTY call stack (innermost first): " + " -> ".join(self.trace))
        return "\n".join(parts)


def fail(kind: str, message: str, location: Location | None = None,
         *, code: str = "Q0000", hint: str = "") -> None:
    raise QwertyError(kind, message, location, code=code, hint=hint)
