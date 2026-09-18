"""Command-line interface; only Python's standard library is required."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from . import __version__, compile_source
from .builtins import REGISTRY
from .bytecode import from_json
from .context import Context
from .errors import QwertyError
from .vm import VirtualMachine


def read_file(path: Path) -> str:
    if path.stat().st_size > 8_000_000:
        raise QwertyError("LimitError", "Input file exceeds 8 MB.", code="Q4001")
    return path.read_text(encoding="utf-8-sig")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="qwerty", description="QWERTY compiler and stack virtual machine")
    parser.add_argument("--version", action="version", version=f"QWERTY {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in [("run", "Execute a .qw or .qbc program"),
                            ("check", "Check syntax and names without executing"),
                            ("compile", "Compile .qw to a .qbc instruction file"),
                            ("bytecode", "Display readable QWERTY instructions")]:
        command = commands.add_parser(name, help=help_text)
        command.add_argument("file", type=Path)
        if name == "run":
            command.add_argument("--input", type=Path, help="Text file containing one line per askit()")
        if name == "compile":
            command.add_argument("-o", "--output", type=Path)
    commands.add_parser("functions", help="List all built-in function signatures")
    editor = commands.add_parser("web", help="Start the local browser editor (not a production server)")
    editor.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        if args.command == "functions":
            print(f"QWERTY {__version__}: {len(REGISTRY)} built-in functions\n")
            for builtin in REGISTRY.values():
                print(f"[{builtin.category}] {builtin.signature}\n  {builtin.description}")
            return 0
        if args.command == "web":
            from .server import serve
            serve(args.port)
            return 0
        contents = read_file(args.file)
        program = from_json(contents) if args.file.suffix.lower() == ".qbc" else compile_source(contents, str(args.file))
        if args.command == "run":
            inputs = read_file(args.input).splitlines() if args.input else ()
            reader = None if args.input else lambda: input()
            context = Context(inputs=inputs, output_sink=sys.stdout.write, input_reader=reader)
            VirtualMachine(program, context).run()
        elif args.command == "check":
            print(f"OK: {args.file} - syntax, names, calls, control flow, and bytecode structure checked.")
            print("Dynamic types and runtime values are checked when the program runs.")
        elif args.command == "bytecode":
            print(program.disassemble())
        elif args.command == "compile":
            output = args.output or args.file.with_suffix(".qbc")
            if output.resolve() == args.file.resolve():
                raise ValueError("Choose an output path different from the input file.")
            output.write_text(program.to_json(), encoding="utf-8")
            print(f"Compiled: {args.file} -> {output}")
        return 0
    except QwertyError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError) as error:
        print(f"QWERTY: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 130
