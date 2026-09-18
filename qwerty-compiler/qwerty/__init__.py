"""Public embedding API for the QWERTY compiler and runtime."""
from __future__ import annotations
from .compiler import compile_source
from .context import Context
from .errors import QwertyError
from .values import Limits
from .vm import ExecutionResult, VirtualMachine

__version__ = "1.0.0"
__all__ = ["compile_source", "execute", "Context", "Limits", "QwertyError", "VirtualMachine", "ExecutionResult"]


def execute(source: str, filename: str = "<source>", *, inputs=(), limits: Limits | None = None,
            output_sink=None, input_reader=None) -> ExecutionResult:
    """Compile all source before running it. Raise QwertyError on diagnostics."""
    program = compile_source(source, filename)
    context = Context(limits, inputs, output_sink, input_reader)
    return VirtualMachine(program, context).run()
