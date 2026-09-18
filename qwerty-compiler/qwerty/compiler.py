"""Resolve lexical names, check calls/control flow, and emit QWERTY opcodes."""
from __future__ import annotations
from difflib import get_close_matches
from .builtins import REGISTRY
from .bytecode import Chunk, Instruction, Op, Program, validate
from .errors import QwertyError, fail
from .lexer import Lexer
from .nodes import Node
from .parser import Parser

NAME_HINTS = {"print": "sayit", "input": "askit", "len": "sizeit", "add": "addit",
              "subtract": "subit", "sum": "sumit", "range": "spanit", "int": "intit",
              "float": "floatit", "str": "textit", "abs": "absit", "max": "maxit",
              "min": "minit", "True": "aye", "False": "nay", "None": "void"}


class ChunkCompiler:
    def __init__(self, chunk: Chunk, globals_map: dict[str, int], signatures: dict[str, int], *, main=False):
        self.chunk, self.globals, self.signatures, self.main = chunk, globals_map, signatures, main
        self.scopes: list[dict[str, int]] = [{}]
        self.loops: list[tuple[int, list[int]]] = []
        if not main:
            for index, name in enumerate(chunk.params):
                self.scopes[0][name] = index

    def emit(self, op: Op, arg=None, node: Node | None = None) -> int:
        index = len(self.chunk.code)
        self.chunk.code.append(Instruction(op, arg, node.location if node else self.chunk.code[-1].location))
        return index

    def patch(self, index: int, target: int) -> None:
        self.chunk.code[index].arg = target

    def fresh(self, name: str) -> int:
        index = len(self.chunk.local_names)
        self.chunk.local_names.append(name)
        return index

    def define(self, name: str, node: Node) -> int:
        if name in REGISTRY or name in self.signatures:
            fail("CompileError", f"{name!r} is reserved for a function.", node.location, code="Q2102")
        if name in self.scopes[-1]:
            fail("CompileError", f"Variable {name!r} is already declared in this scope.", node.location,
                 code="Q2102", hint="Use assignment without 'keep' to change its value.")
        slot = self.globals[name] if self.main and len(self.scopes) == 1 else self.fresh(name)
        self.scopes[-1][name] = slot
        return slot

    def resolve(self, name: str, node: Node) -> tuple[bool, int]:
        for scope in reversed(self.scopes):
            if name in scope:
                return False, scope[name]
        if not self.main and name in self.globals:
            return True, self.globals[name]
        hint = f"Use {NAME_HINTS[name]!r} instead." if name in NAME_HINTS else "Declare the variable with 'keep' before using it."
        fail("CompileError", f"Unknown variable {name!r}.", node.location, code="Q2101", hint=hint)

    def block(self, node: Node) -> None:
        self.scopes.append({})
        for statement in node.children:
            self.statement(statement)
        self.scopes.pop()

    def statement(self, node: Node) -> None:
        kind = node.kind
        if kind == "block":
            self.block(node)
        elif kind == "keep":
            self.expression(node.children[0])
            slot = self.define(node.value, node)
            self.emit(Op.STORE_LOCAL, slot, node)
        elif kind == "assign":
            global_slot, slot = self.resolve(node.value, node)
            self.expression(node.children[0])
            self.emit(Op.STORE_GLOBAL if global_slot else Op.STORE_LOCAL, slot, node)
        elif kind == "expression":
            self.expression(node.children[0])
            self.emit(Op.POP, node=node)
        elif kind == "if":
            self.expression(node.children[0])
            otherwise = self.emit(Op.JUMP_FALSE, -1, node)
            self.statement(node.children[1])
            end = self.emit(Op.JUMP, -1, node)
            self.patch(otherwise, len(self.chunk.code))
            if len(node.children) == 3:
                self.statement(node.children[2])
            self.patch(end, len(self.chunk.code))
        elif kind == "while":
            start = len(self.chunk.code)
            self.expression(node.children[0])
            end = self.emit(Op.JUMP_FALSE, -1, node)
            breaks: list[int] = []
            self.loops.append((start, breaks))
            self.statement(node.children[1])
            self.loops.pop()
            self.emit(Op.JUMP, start, node)
            self.patch(end, len(self.chunk.code))
            for index in breaks:
                self.patch(index, len(self.chunk.code))
        elif kind == "each":
            self.expression(node.children[0])
            self.emit(Op.ITER, node=node)
            iterator_slot = self.fresh(f"<iterator:{len(self.chunk.local_names)}>")
            self.emit(Op.STORE_LOCAL, iterator_slot, node)
            self.scopes.append({})
            item_slot = self.define(node.value, node)
            start = len(self.chunk.code)
            next_index = self.emit(Op.ITER_NEXT, [iterator_slot, -1], node)
            self.emit(Op.STORE_LOCAL, item_slot, node)
            breaks = []
            self.loops.append((start, breaks))
            self.statement(node.children[1])
            self.loops.pop()
            self.emit(Op.JUMP, start, node)
            self.chunk.code[next_index].arg[1] = len(self.chunk.code)
            for index in breaks:
                self.patch(index, len(self.chunk.code))
            self.scopes.pop()
        elif kind in {"stop", "skip"}:
            if not self.loops:
                fail("CompileError", f"'{kind}' is only valid inside a loop.", node.location, code="Q2103")
            start, breaks = self.loops[-1]
            index = self.emit(Op.JUMP, start if kind == "skip" else -1, node)
            if kind == "stop":
                breaks.append(index)
        elif kind == "return":
            if self.main:
                fail("CompileError", "'give' is only valid inside a crafted function.", node.location, code="Q2103")
            if node.children:
                self.expression(node.children[0])
            else:
                self.emit(Op.CONST, None, node)
            self.emit(Op.RETURN, node=node)
        elif kind == "function":
            fail("CompileError", "Crafted functions must be declared at the top level.", node.location,
                 code="Q2103", hint="Nested functions and closures are not part of QWERTY v1.")
        else:
            raise AssertionError(f"Unsupported AST statement {kind}")

    def expression(self, node: Node) -> None:
        kind = node.kind
        if kind == "literal":
            self.emit(Op.CONST, node.value, node)
        elif kind == "name":
            global_slot, slot = self.resolve(node.value, node)
            self.emit(Op.LOAD_GLOBAL if global_slot else Op.LOAD_LOCAL, slot, node)
        elif kind == "list":
            for child in node.children:
                self.expression(child)
            self.emit(Op.BUILD_LIST, len(node.children), node)
        elif kind == "index":
            for child in node.children:
                self.expression(child)
            self.emit(Op.INDEX, node=node)
        elif kind == "unary":
            self.expression(node.children[0])
            self.emit(Op.UNARY, node.value, node)
        elif kind == "binary":
            self.expression(node.children[0])
            if node.value in {"&&", "||"}:
                self.emit(Op.BOOL, node=node)
                jump = self.emit(Op.JUMP_FALSE_KEEP if node.value == "&&" else Op.JUMP_TRUE_KEEP, -1, node)
                self.emit(Op.POP, node=node)
                self.expression(node.children[1])
                self.emit(Op.BOOL, node=node)
                self.patch(jump, len(self.chunk.code))
            else:
                self.expression(node.children[1])
                self.emit(Op.BINARY, node.value, node)
        elif kind == "call":
            name, count = node.value, len(node.children)
            if name in REGISTRY:
                builtin = REGISTRY[name]
                okay, expected = builtin.accepts(count), builtin.arity_description()
            elif name in self.signatures:
                expected = str(self.signatures[name])
                okay = count == self.signatures[name]
            else:
                match = get_close_matches(name, [*REGISTRY, *self.signatures], n=1, cutoff=0.5)
                suggestion = NAME_HINTS.get(name, match[0] if match else "")
                fail("CompileError", f"Unknown function {name!r}.", node.location, code="Q2104",
                     hint=f"Use {suggestion}()." if suggestion else "Use a standard function or define one with 'craft'.")
            if not okay:
                fail("CompileError", f"{name}() expects {expected} argument(s), received {count}.",
                     node.location, code="Q2105")
            for child in node.children:
                self.expression(child)
            self.emit(Op.CALL, [name, count], node)
        else:
            raise AssertionError(f"Unsupported AST expression {kind}")


def compile_source(source: str, filename: str = "<source>") -> Program:
    # Normalize line endings so API inputs and files share diagnostic locations.
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    try:
        tokens = Lexer(source).tokenize()
        nodes = Parser(tokens).parse()
        functions = {}
        signatures = {}
        globals_map = {}
        for node in nodes:
            if node.kind == "function":
                name = node.token.text
                params = [p.text for p in node.value]
                if name in REGISTRY or name in signatures:
                    fail("CompileError", f"Function {name!r} is already defined or reserved.", node.location, code="Q2102")
                if len(params) > 256 or len(set(params)) != len(params):
                    fail("CompileError", "Function parameters must be unique; maximum 256.", node.location, code="Q2102")
                signatures[name] = len(params)
                functions[name] = Chunk(name, params, params.copy())
            elif node.kind == "keep":
                if node.value in globals_map:
                    fail("CompileError", f"Global variable {node.value!r} is already declared.", node.location, code="Q2102")
                globals_map[node.value] = len(globals_map)
        global_names = list(globals_map)
        main = Chunk("<main>", [], global_names.copy())
        compiler = ChunkCompiler(main, globals_map, signatures, main=True)
        for node in nodes:
            if node.kind != "function":
                compiler.statement(node)
        main.code.append(Instruction(Op.HALT, location=tokens[-1].location))
        for node in nodes:
            if node.kind != "function":
                continue
            chunk = functions[node.token.text]
            for param in node.value:
                if param.text in REGISTRY or param.text in signatures:
                    fail("CompileError", f"Parameter {param.text!r} conflicts with a function name.", param.location, code="Q2102")
            compiler = ChunkCompiler(chunk, globals_map, signatures)
            # Parameters and the outer function body deliberately share one scope.
            for statement in node.children[0].children:
                compiler.statement(statement)
            chunk.code.extend([Instruction(Op.CONST, None, node.location), Instruction(Op.RETURN, None, node.location)])
        program = Program(filename, source, global_names, main, functions)
        validate(program)
        return program
    except QwertyError as error:
        raise error.attach(source, filename) from None
    except RecursionError:
        error = QwertyError("LimitError", "Expression or block nesting is too deep.", code="Q4004")
        raise error.attach(source, filename) from None
