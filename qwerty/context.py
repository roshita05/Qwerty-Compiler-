"""Per-run I/O and execution budgets; no global program state."""
from __future__ import annotations
from collections import deque
from time import monotonic
from typing import Callable, Iterable
from .errors import fail
from .values import Limits, text, check_length


class Context:
    def __init__(self, limits: Limits | None = None, inputs: Iterable[str] = (),
                 output_sink: Callable[[str], None] | None = None,
                 input_reader: Callable[[], str] | None = None):
        self.limits = limits or Limits()
        self.inputs = deque(inputs)
        self.output_sink, self.input_reader = output_sink, input_reader
        self.output: list[str] = []
        self.output_size = self.steps = 0
        self.deadline = monotonic() + self.limits.timeout_seconds

    def check_time(self):
        if monotonic() > self.deadline:
            fail("LimitError", "Execution time limit exceeded.", code="Q4011",
                 hint="Check loops or use smaller input collections.")

    def tick(self):
        self.steps += 1
        if self.steps > self.limits.max_steps:
            fail("LimitError", "Instruction limit exceeded.", code="Q4012",
                 hint="A loop may never finish. Check its condition and updates.")
        self.check_time()

    def emit(self, value: str):
        check_length(self.output_size + len(value), self.limits.max_output, "Program output")
        self.output.append(value)
        self.output_size += len(value)
        if self.output_sink is not None:
            self.output_sink(value)

    def read(self, prompt: str = "") -> str:
        self.emit(text(prompt))
        if self.inputs:
            result = text(self.inputs.popleft())
        elif self.input_reader is not None:
            # Human input waiting is intentionally excluded from the runtime timer.
            start = monotonic()
            try:
                result = text(self.input_reader())
            except EOFError:
                fail("InputError", "No more input is available.", code="Q3007")
            finally:
                self.deadline += monotonic() - start
        else:
            fail("InputError", "askit() needs another input line.", code="Q3007",
                 hint="Add one input line per askit() call in the editor's Program input box.")
        check_length(len(result), self.limits.max_string, "Input line length")
        return result
