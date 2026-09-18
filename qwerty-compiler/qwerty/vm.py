"""Stack VM with explicit call frames, budgets, and structured runtime errors."""
from __future__ import annotations
from dataclasses import dataclass, field
from .builtins import REGISTRY
from .bytecode import Chunk, Op, Program
from .context import Context
from .errors import QwertyError, fail
from .values import arithmetic, collection, equal, guard, number, ordered, pick

UNSET = object()


@dataclass
class IteratorState:
    values: object
    index: int = 0


@dataclass
class Frame:
    chunk: Chunk
    locals: list
    stack: list = field(default_factory=list)
    pc: int = 0


@dataclass
class ExecutionResult:
    output: str
    globals: dict
    steps: int
    program: Program


class VirtualMachine:
    def __init__(self, program: Program, context: Context):
        self.program, self.context = program, context
        self.main = Frame(program.main, [UNSET] * len(program.main.local_names))
        self.frames = [self.main]

    def runtime_error(self, error: QwertyError, instruction) -> None:
        error.location = instruction.location
        error.trace = [frame.chunk.name for frame in reversed(self.frames)]
        error.output = "".join(self.context.output)
        raise error.attach(self.program.source, self.program.filename) from None

    def run(self) -> ExecutionResult:
        context, program = self.context, self.program
        while self.frames:
            frame = self.frames[-1]
            instruction = frame.chunk.code[frame.pc]
            frame.pc += 1
            op, arg, stack = instruction.op, instruction.arg, frame.stack
            try:
                context.tick()
                if op == Op.CONST:
                    guard(arg, context.limits)
                    stack.append(arg)
                elif op in {Op.LOAD_LOCAL, Op.LOAD_GLOBAL}:
                    target = self.main if op == Op.LOAD_GLOBAL else frame
                    value = target.locals[arg]
                    if value is UNSET:
                        name = target.chunk.local_names[arg]
                        fail("RuntimeError", f"Variable {name!r} was used before it was initialized.", code="Q3001",
                             hint="Initialize global variables before calling functions that read them.")
                    if isinstance(value, IteratorState):
                        fail("BytecodeError", "Internal iterators cannot be read as language values.", code="Q5001")
                    stack.append(value)
                elif op in {Op.STORE_LOCAL, Op.STORE_GLOBAL}:
                    target = self.main if op == Op.STORE_GLOBAL else frame
                    if op == Op.STORE_GLOBAL and target.locals[arg] is UNSET:
                        fail("RuntimeError", "Cannot assign a global before its declaration has executed.", code="Q3001")
                    target.locals[arg] = stack.pop()
                elif op == Op.POP:
                    stack.pop()
                elif op == Op.BUILD_LIST:
                    values = stack[-arg:] if arg else []
                    if arg:
                        del stack[-arg:]
                    guard(values, context.limits)
                    stack.append(values)
                elif op == Op.INDEX:
                    index, values = stack.pop(), stack.pop()
                    stack.append(pick(values, index))
                elif op == Op.UNARY:
                    value = stack.pop()
                    result = not value if arg == "!" else (-number(value) if arg == "-" else number(value))
                    guard(result, context.limits)
                    stack.append(result)
                elif op == Op.BINARY:
                    right, left = stack.pop(), stack.pop()
                    if arg == "==":
                        result = equal(left, right)
                    elif arg == "!=":
                        result = not equal(left, right)
                    elif arg in {"<", "<=", ">", ">="}:
                        result = ordered(left, right, arg)
                    else:
                        result = arithmetic(arg, left, right, context.limits)
                    guard(result, context.limits)
                    stack.append(result)
                elif op == Op.BOOL:
                    stack.append(bool(stack.pop()))
                elif op == Op.JUMP:
                    frame.pc = arg
                elif op == Op.JUMP_FALSE:
                    if not stack.pop():
                        frame.pc = arg
                elif op == Op.JUMP_FALSE_KEEP:
                    if not stack[-1]:
                        frame.pc = arg
                elif op == Op.JUMP_TRUE_KEEP:
                    if stack[-1]:
                        frame.pc = arg
                elif op == Op.CALL:
                    name, count = arg
                    args = stack[-count:] if count else []
                    if count:
                        del stack[-count:]
                    if name in REGISTRY:
                        result = REGISTRY[name].implementation(context, *args)
                        guard(result, context.limits)
                        context.check_time()
                        stack.append(result)
                    else:
                        if len(self.frames) >= context.limits.max_call_depth + 1:
                            fail("LimitError", "Function call-depth limit exceeded.", code="Q4013",
                                 hint="Check the base case of recursive functions.")
                        chunk = program.functions[name]
                        locals_ = [UNSET] * len(chunk.local_names)
                        locals_[:len(args)] = args
                        self.frames.append(Frame(chunk, locals_))
                elif op == Op.RETURN:
                    result = stack.pop()
                    self.frames.pop()
                    self.frames[-1].stack.append(result)
                elif op == Op.ITER:
                    values = collection(stack.pop())
                    stack.append(IteratorState(list(values) if type(values) is dict else values))
                elif op == Op.ITER_NEXT:
                    slot, end = arg
                    iterator = frame.locals[slot]
                    if not isinstance(iterator, IteratorState):
                        fail("BytecodeError", "ITER_NEXT requires an initialized internal iterator.", code="Q5001")
                    if iterator.index >= len(iterator.values):
                        frame.pc = end
                    else:
                        stack.append(iterator.values[iterator.index])
                        iterator.index += 1
                elif op == Op.HALT:
                    break
                else:
                    fail("BytecodeError", "Unsupported instruction.", code="Q5001")
            except QwertyError as error:
                self.runtime_error(error, instruction)
            except (MemoryError, RecursionError):
                self.runtime_error(QwertyError("LimitError", "Operation exceeded resource limits.", code="Q4014"), instruction)
            except ZeroDivisionError:
                self.runtime_error(QwertyError("RuntimeError", "Division by zero is not allowed.", code="Q3002"), instruction)
            except (ValueError, OverflowError) as error:
                self.runtime_error(QwertyError("RuntimeError", f"Invalid value: {error}", code="Q3008"), instruction)
            except (TypeError, IndexError, KeyError) as error:
                self.runtime_error(QwertyError("RuntimeError", f"Invalid operation: {error}", code="Q3010"), instruction)
        globals_ = {name: self.main.locals[index] for index, name in enumerate(program.global_names)
                    if self.main.locals[index] is not UNSET}
        return ExecutionResult("".join(context.output), globals_, context.steps, program)
