"""A compact, inspectable abstract syntax tree."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .lexer import Token


@dataclass
class Node:
    kind: str
    token: Token
    value: Any = None
    children: list[Node] = field(default_factory=list)

    @property
    def location(self):
        return self.token.location
