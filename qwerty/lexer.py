"""Tokenize QWERTY directly; never rewrite or evaluate Python source."""
from __future__ import annotations
from dataclasses import dataclass
import math
import re
from .errors import Location, fail

KEYWORDS = {"keep", "craft", "give", "when", "otherwise", "whilst", "each",
            "over", "stop", "skip", "aye", "nay", "void"}
NUMBER = re.compile(r"(?:\d+(?:\.\d+)?)(?:[eE][+-]?\d+)?", re.ASCII)
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*", re.ASCII)
MAX_SOURCE = 100_000
MAX_TOKENS = 30_000


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    value: object
    location: Location


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position, self.line, self.column = 0, 1, 1

    def advance(self, text: str) -> None:
        self.position += len(text)
        if "\n" in text:
            self.line += text.count("\n")
            self.column = len(text.rsplit("\n", 1)[1]) + 1
        else:
            self.column += len(text)

    def scan_string(self, quote: str, location: Location) -> Token:
        start = self.position
        self.advance(quote)
        chars: list[str] = []
        escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", "\"": "\"", "'": "'"}
        while self.position < len(self.source):
            char = self.source[self.position]
            if char == quote:
                self.advance(char)
                return Token("STRING", self.source[start:self.position], "".join(chars), location)
            if char in "\r\n":
                fail("LexicalError", "Unterminated string literal.", location, code="Q1002",
                     hint="Close the quote before the line ends; use \\n for a newline.")
            if char != "\\":
                chars.append(char)
                self.advance(char)
                continue
            escape_location = Location(self.line, self.column)
            self.advance(char)
            if self.position >= len(self.source):
                break
            char = self.source[self.position]
            if char == "u":
                text = self.source[self.position + 1:self.position + 5]
                if len(text) != 4 or any(c not in "0123456789abcdefABCDEF" for c in text):
                    fail("LexicalError", "Expected four hex digits after \\u.", escape_location, code="Q1003")
                point = int(text, 16)
                if 0xD800 <= point <= 0xDFFF:
                    fail("LexicalError", "A Unicode surrogate is not a standalone character.", escape_location, code="Q1003")
                chars.append(chr(point))
                self.advance("u" + text)
            elif char in escapes:
                chars.append(escapes[char])
                self.advance(char)
            else:
                fail("LexicalError", f"Unknown string escape \\{char}.", escape_location, code="Q1003")
        fail("LexicalError", "Unterminated string literal.", location, code="Q1002")

    def tokenize(self) -> list[Token]:
        if len(self.source) > MAX_SOURCE:
            fail("LimitError", f"Source exceeds {MAX_SOURCE:,} characters.", code="Q4001")
        tokens: list[Token] = []
        while self.position < len(self.source):
            location = Location(self.line, self.column)
            char = self.source[self.position]
            if char.isspace():
                self.advance(char)
                continue
            if char == "#":
                end = self.source.find("\n", self.position)
                self.advance(self.source[self.position:end if end != -1 else len(self.source)])
                continue
            if self.source.startswith("/*", self.position):
                end = self.source.find("*/", self.position + 2)
                if end == -1:
                    fail("LexicalError", "Unterminated block comment.", location, code="Q1004")
                self.advance(self.source[self.position:end + 2])
                continue
            if char in "\"'":
                tokens.append(self.scan_string(char, location))
            elif match := NUMBER.match(self.source, self.position):
                text = match.group()
                if len(text) > 1_000:
                    fail("LimitError", "Numeric literal is too long.", location, code="Q4002")
                try:
                    value = float(text) if any(c in text for c in ".eE") else int(text)
                except ValueError:
                    fail("LexicalError", "Invalid number.", location, code="Q1005")
                if isinstance(value, float) and not math.isfinite(value):
                    fail("LexicalError", "Numbers must be finite.", location, code="Q1005")
                tokens.append(Token("NUMBER", text, value, location))
                self.advance(text)
            elif match := IDENTIFIER.match(self.source, self.position):
                text = match.group()
                if text.startswith("__"):
                    fail("LexicalError", "Names beginning with '__' are reserved.", location, code="Q1006")
                tokens.append(Token(text if text in KEYWORDS else "NAME", text, text, location))
                self.advance(text)
            else:
                pair = self.source[self.position:self.position + 2]
                if pair in {"==", "!=", "<=", ">=", "&&", "||", "**", "//"}:
                    text = pair
                elif char in "+-*/%=<>!(){}[],;":
                    text = char
                else:
                    fail("LexicalError", f"Unexpected character {char!r}.", location, code="Q1001",
                         hint="QWERTY has no Python imports or attribute access; comments start with #.")
                tokens.append(Token(text, text, text, location))
                self.advance(text)
            if len(tokens) > MAX_TOKENS:
                fail("LimitError", "Program contains too many tokens.", location, code="Q4003")
        tokens.append(Token("EOF", "", None, Location(self.line, self.column)))
        return tokens
