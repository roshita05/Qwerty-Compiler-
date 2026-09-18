"""Recursive-descent statements and precedence-climbing expressions."""
from __future__ import annotations
from .errors import fail
from .lexer import Token
from .nodes import Node

PRECEDENCE = {"||": 1, "&&": 2, "==": 3, "!=": 3, "<": 4, "<=": 4, ">": 4,
              ">=": 4, "+": 5, "-": 5, "*": 6, "/": 6, "//": 6, "%": 6, "**": 8}
PYTHON_HINTS = {"print": "sayit", "input": "askit", "len": "sizeit", "def": "craft",
                "if": "when", "else": "otherwise", "while": "whilst", "for": "each",
                "return": "give", "True": "aye", "False": "nay", "None": "void"}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens, self.position, self.depth = tokens, 0, 0

    @property
    def current(self) -> Token:
        return self.tokens[self.position]

    def take(self) -> Token:
        token = self.current
        self.position += 1
        return token

    def match(self, *kinds: str) -> Token | None:
        return self.take() if self.current.kind in kinds else None

    def expect(self, kind: str, message: str = "") -> Token:
        if self.current.kind != kind:
            hint = "End simple statements with ';'." if kind == ";" else ""
            if self.current.text in PYTHON_HINTS:
                hint = f"Use {PYTHON_HINTS[self.current.text]!r}, not {self.current.text!r}."
            fail("SyntaxError", message or f"Expected {kind!r}, found {self.current.text or 'end of file'!r}.",
                 self.current.location, code="Q2001", hint=hint)
        return self.take()

    def enter(self) -> None:
        self.depth += 1
        if self.depth > 80:
            fail("LimitError", "Program is nested too deeply.", self.current.location, code="Q4004")

    def parse(self) -> list[Node]:
        result: list[Node] = []
        while self.current.kind != "EOF":
            result.append(self.statement())
        return result

    def block(self) -> Node:
        token = self.expect("{")
        self.enter()
        statements: list[Node] = []
        while self.current.kind not in {"}", "EOF"}:
            statements.append(self.statement())
        self.expect("}", "Expected '}' to close the block.")
        self.depth -= 1
        return Node("block", token, children=statements)

    def statement(self) -> Node:
        token = self.current
        if self.match("keep"):
            name = self.expect("NAME", "Expected a variable name after 'keep'.")
            self.expect("=")
            value = self.expression()
            self.expect(";")
            return Node("keep", name, name.text, [value])
        if self.match("craft"):
            name = self.expect("NAME", "Expected a function name after 'craft'.")
            self.expect("(")
            params: list[Token] = []
            if self.current.kind != ")":
                while True:
                    params.append(self.expect("NAME"))
                    if not self.match(","):
                        break
            self.expect(")")
            return Node("function", name, params, [self.block()])
        if self.match("when"):
            condition = self.expression()
            yes = self.block()
            children = [condition, yes]
            if self.match("otherwise"):
                children.append(self.statement() if self.current.kind == "when" else self.block())
            return Node("if", token, children=children)
        if self.match("whilst"):
            return Node("while", token, children=[self.expression(), self.block()])
        if self.match("each"):
            name = self.expect("NAME", "Expected a loop variable after 'each'.")
            self.expect("over")
            return Node("each", name, name.text, [self.expression(), self.block()])
        if self.match("give"):
            children = [] if self.current.kind == ";" else [self.expression()]
            self.expect(";")
            return Node("return", token, children=children)
        if self.match("stop", "skip"):
            self.expect(";")
            return Node(token.kind, token)
        if self.current.kind == "{":
            return self.block()
        expression = self.expression()
        if self.match("="):
            if expression.kind != "name":
                fail("SyntaxError", "Only a variable name can be assigned to.", expression.location,
                     code="Q2002", hint="Use items = putit(items, index, value) to update a list.")
            value = self.expression()
            self.expect(";")
            return Node("assign", expression.token, expression.value, [value])
        self.expect(";")
        return Node("expression", token, children=[expression])

    def expression(self, minimum: int = 1) -> Node:
        self.enter()
        token = self.current
        if self.match("-", "+", "!"):
            left = Node("unary", token, token.kind, [self.expression(7)])
        elif self.match("NUMBER", "STRING"):
            left = Node("literal", token, token.value)
        elif self.match("aye", "nay", "void"):
            left = Node("literal", token, {"aye": True, "nay": False, "void": None}[token.kind])
        elif self.match("NAME"):
            left = Node("name", token, token.text)
        elif self.match("("):
            left = self.expression()
            self.expect(")")
        elif self.match("["):
            values: list[Node] = []
            if self.current.kind != "]":
                while True:
                    values.append(self.expression())
                    if not self.match(",") or self.current.kind == "]":
                        break
            self.expect("]")
            left = Node("list", token, children=values)
        else:
            fail("SyntaxError", f"Expected an expression, found {token.text or 'end of file'!r}.",
                 token.location, code="Q2003")
        while True:
            if self.current.kind == "(":
                if left.kind != "name":
                    fail("SyntaxError", "Call a named function, such as addit(2, 3).", self.current.location, code="Q2004")
                self.take()
                args: list[Node] = []
                if self.current.kind != ")":
                    while True:
                        args.append(self.expression())
                        if len(args) > 256:
                            fail("LimitError", "A call may have at most 256 arguments.", token.location, code="Q4005")
                        if not self.match(","):
                            break
                self.expect(")")
                left = Node("call", left.token, left.value, args)
                continue
            if self.match("["):
                index = self.expression()
                self.expect("]")
                left = Node("index", left.token, children=[left, index])
                continue
            precedence = PRECEDENCE.get(self.current.kind, 0)
            if precedence < minimum:
                break
            operator = self.take()
            right = self.expression(precedence if operator.kind == "**" else precedence + 1)
            left = Node("binary", operator, operator.kind, [left, right])
        self.depth -= 1
        return left
