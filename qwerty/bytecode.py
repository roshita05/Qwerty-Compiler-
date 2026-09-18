"""Versioned QWERTY instruction format, disassembly, and checked persistence.

.qbc is a JSON-encoded instruction stream, not Python bytecode or native code.
Numeric opcodes run only on the QWERTY VM. No pickle or executable deserialization.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
import json
from .errors import Location, QwertyError, fail
from .values import Limits, guard


class Op(IntEnum):
    CONST = 1
    LOAD_LOCAL = 2
    STORE_LOCAL = 3
    LOAD_GLOBAL = 4
    STORE_GLOBAL = 5
    POP = 6
    BUILD_LIST = 7
    INDEX = 8
    UNARY = 9
    BINARY = 10
    BOOL = 11
    JUMP = 12
    JUMP_FALSE = 13
    JUMP_FALSE_KEEP = 14
    JUMP_TRUE_KEEP = 15
    CALL = 16
    RETURN = 17
    ITER = 18
    ITER_NEXT = 19
    HALT = 20


@dataclass
class Instruction:
    op: Op
    arg: object = None
    location: Location = field(default_factory=Location)


@dataclass
class Chunk:
    name: str
    params: list[str]
    local_names: list[str]
    code: list[Instruction] = field(default_factory=list)


@dataclass
class Program:
    filename: str
    source: str
    global_names: list[str]
    main: Chunk
    functions: dict[str, Chunk]

    def disassemble(self) -> str:
        parts = []
        for chunk in [self.main, *self.functions.values()]:
            parts.append(f"== {chunk.name}({', '.join(chunk.params)}) | {len(chunk.local_names)} slots ==")
            for index, ins in enumerate(chunk.code):
                operand = "" if ins.arg is None else repr(ins.arg)
                if len(operand) > 140:
                    operand = operand[:137] + "..."
                parts.append(f"{index:04d}  {ins.location.line:>4}:{ins.location.column:<3}  {ins.op.name:<17} {operand}")
            parts.append("")
        return "\n".join(parts)

    def to_json(self) -> str:
        def chunk_data(chunk):
            return {"name": chunk.name, "params": chunk.params, "locals": chunk.local_names,
                    "code": [[int(i.op), i.arg, i.location.line, i.location.column] for i in chunk.code]}
        return json.dumps({"format": "QWERTY-BC", "version": 1, "filename": self.filename,
                           "source": self.source, "globals": self.global_names,
                           "main": chunk_data(self.main),
                           "functions": {k: chunk_data(v) for k, v in self.functions.items()}},
                          ensure_ascii=True, allow_nan=False, indent=2)


def invalid(message):
    fail("BytecodeError", message, code="Q5001",
         hint="Recompile the original .qw file with this QWERTY version.")


def validate(program: Program) -> None:
    """Validate operands and reachable stack heights before executing a file."""
    from .builtins import REGISTRY
    from .lexer import IDENTIFIER, MAX_SOURCE

    def valid_name(value):
        return type(value) is str and bool(IDENTIFIER.fullmatch(value)) and not value.startswith("__")

    if not isinstance(program.source, str) or len(program.source) > MAX_SOURCE:
        invalid("Invalid embedded source.")
    if type(program.filename) is not str or len(program.filename) > 4_096:
        invalid("Invalid source filename.")
    if (any(not valid_name(n) for n in program.global_names)
            or len(set(program.global_names)) != len(program.global_names)):
        invalid("Invalid global variable names.")
    if program.main.name != "<main>" or program.main.params:
        invalid("Invalid main chunk.")
    if program.main.local_names[:len(program.global_names)] != program.global_names:
        invalid("Global slots do not match the main chunk.")
    if len(program.functions) > 1_000:
        invalid("Too many functions.")
    for name, chunk in program.functions.items():
        if not valid_name(name) or name in REGISTRY or chunk.name != name:
            invalid("Invalid function name.")
    total = 0
    for chunk in [program.main, *program.functions.values()]:
        code = chunk.code
        total += len(code)
        if not code or total > 60_000 or len(chunk.local_names) > 30_000:
            invalid("Invalid instruction or local-variable count.")
        if (len(chunk.params) > 256 or len(set(chunk.params)) != len(chunk.params)
                or any(not valid_name(n) for n in chunk.params)
                or chunk.local_names[:len(chunk.params)] != chunk.params):
            invalid("Invalid function parameters.")
        if any(type(n) is not str or len(n) > 1_000 for n in chunk.local_names):
            invalid("Invalid local names.")

        def slot(value, maximum):
            return type(value) is int and 0 <= value < maximum

        def target(value):
            return slot(value, len(code))

        for ins in code:
            op, arg = ins.op, ins.arg
            if not (type(ins.location.line) is int and type(ins.location.column) is int
                    and 1 <= ins.location.line <= 100_001 and 1 <= ins.location.column <= 100_001):
                invalid("Invalid instruction location.")
            if op == Op.CONST:
                if type(arg) not in (type(None), bool, int, float, str):
                    invalid("A constant must be a scalar QWERTY value.")
                guard(arg, Limits())
            elif op in {Op.LOAD_LOCAL, Op.STORE_LOCAL}:
                if not slot(arg, len(chunk.local_names)):
                    invalid("Invalid local-variable slot.")
            elif op in {Op.LOAD_GLOBAL, Op.STORE_GLOBAL}:
                if not slot(arg, len(program.global_names)):
                    invalid("Invalid global-variable slot.")
            elif op == Op.BUILD_LIST:
                if type(arg) is not int or not 0 <= arg <= 10_000:
                    invalid("Invalid list size.")
            elif op == Op.UNARY:
                if arg not in ("+", "-", "!"):
                    invalid("Invalid unary operator.")
            elif op == Op.BINARY:
                if arg not in ("+", "-", "*", "/", "//", "%", "**", "==", "!=", "<", ">", "<=", ">="):
                    invalid("Invalid binary operator.")
            elif op in {Op.JUMP, Op.JUMP_FALSE, Op.JUMP_FALSE_KEEP, Op.JUMP_TRUE_KEEP}:
                if not target(arg):
                    invalid("Invalid jump destination.")
            elif op == Op.ITER_NEXT:
                if not (type(arg) is list and len(arg) == 2 and slot(arg[0], len(chunk.local_names)) and target(arg[1])):
                    invalid("Invalid iteration operand.")
            elif op == Op.CALL:
                if not (type(arg) is list and len(arg) == 2 and type(arg[0]) is str and type(arg[1]) is int):
                    invalid("Invalid call operand.")
                name, count = arg
                if name in REGISTRY:
                    if not REGISTRY[name].accepts(count):
                        invalid("Incorrect built-in argument count.")
                elif name not in program.functions or count != len(program.functions[name].params):
                    invalid("Unknown function or incorrect argument count.")
            elif op in {Op.POP, Op.INDEX, Op.BOOL, Op.RETURN, Op.ITER, Op.HALT}:
                if arg is not None:
                    invalid("Unexpected instruction operand.")
                if op == Op.RETURN and chunk is program.main:
                    invalid("Main cannot return to a caller.")
                if op == Op.HALT and chunk is not program.main:
                    invalid("Only main may halt execution.")
            else:
                invalid("Unknown opcode.")

        heights: dict[int, int] = {}
        pending = [(0, 0)]
        while pending:
            pc, height = pending.pop()
            if pc in heights:
                if heights[pc] != height:
                    invalid("Inconsistent stack height at a control-flow join.")
                continue
            if not target(pc):
                invalid("Execution could leave a chunk without RETURN or HALT.")
            heights[pc] = height
            ins = code[pc]
            op, arg = ins.op, ins.arg
            required, change = 0, 0
            if op in {Op.CONST, Op.LOAD_LOCAL, Op.LOAD_GLOBAL}:
                change = 1
            elif op in {Op.STORE_LOCAL, Op.STORE_GLOBAL, Op.POP, Op.JUMP_FALSE, Op.RETURN}:
                required, change = 1, -1
            elif op == Op.BUILD_LIST:
                required, change = arg, 1 - arg
            elif op in {Op.INDEX, Op.BINARY}:
                required, change = 2, -1
            elif op in {Op.UNARY, Op.BOOL, Op.ITER, Op.JUMP_FALSE_KEEP, Op.JUMP_TRUE_KEEP}:
                required = 1
            elif op == Op.CALL:
                required, change = arg[1], 1 - arg[1]
            if height < required or height + change > 30_000:
                invalid("Invalid operand stack use.")
            next_height = height + change
            if op in {Op.RETURN, Op.HALT}:
                if next_height != 0:
                    invalid("A finished chunk must leave an empty operand stack.")
            elif op == Op.JUMP:
                pending.append((arg, next_height))
            elif op in {Op.JUMP_FALSE, Op.JUMP_FALSE_KEEP, Op.JUMP_TRUE_KEEP}:
                pending.extend([(arg, next_height), (pc + 1, next_height)])
            elif op == Op.ITER_NEXT:
                pending.extend([(arg[1], height), (pc + 1, height + 1)])
            else:
                pending.append((pc + 1, next_height))


def from_json(data: str) -> Program:
    if len(data) > 8_000_000:
        invalid("Bytecode file exceeds the size limit.")
    try:
        payload = json.loads(data)
        if type(payload) is not dict or payload.get("format") != "QWERTY-BC" or payload.get("version") != 1:
            invalid("Unsupported bytecode format or version.")

        def read_chunk(value):
            if type(value) is not dict or type(value["code"]) is not list:
                invalid("Invalid chunk structure.")
            if type(value["params"]) is not list or type(value["locals"]) is not list:
                invalid("Invalid slot structure.")
            instructions = []
            for row in value["code"]:
                if type(row) is not list or len(row) != 4 or type(row[0]) is not int:
                    invalid("Invalid instruction encoding.")
                instructions.append(Instruction(Op(row[0]), row[1], Location(row[2], row[3])))
            return Chunk(value["name"], value["params"], value["locals"], instructions)

        if type(payload["functions"]) is not dict or type(payload["globals"]) is not list:
            invalid("Invalid program structure.")
        program = Program(payload["filename"], payload["source"], payload["globals"],
                          read_chunk(payload["main"]),
                          {k: read_chunk(v) for k, v in payload["functions"].items()})
        validate(program)
        return program
    except QwertyError:
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError, OverflowError):
        invalid("Malformed bytecode file.")
