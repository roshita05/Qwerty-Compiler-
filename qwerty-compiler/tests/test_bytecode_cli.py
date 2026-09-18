from __future__ import annotations
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from qwerty import Context, QwertyError, VirtualMachine, compile_source, execute
from qwerty.bytecode import Op, from_json
from qwerty.cli import main

ROOT = Path(__file__).resolve().parent.parent


class BytecodeTests(unittest.TestCase):
    def test_roundtrip(self):
        source = (ROOT / 'examples' / 'demo.qw').read_text()
        program = compile_source(source)
        restored = from_json(program.to_json())
        result = VirtualMachine(restored, Context()).run()
        original = execute(source)
        self.assertEqual(result.output, original.output)
        self.assertEqual(result.globals, original.globals)

    def test_all_valid_examples(self):
        for path in (ROOT / 'examples').glob('*.qw'):
            if path.stem == 'error_demo':
                continue
            with self.subTest(example=path.name):
                program = from_json(compile_source(path.read_text()).to_json())
                VirtualMachine(program, Context(inputs=['Ada', '25'])).run()

    def test_disassembly_contains_custom_opcodes(self):
        listing = compile_source('sayit(addit(1, 2));').disassemble()
        self.assertIn('CONST', listing)
        self.assertIn('CALL', listing)
        self.assertIn('addit', listing)
        self.assertIn('HALT', listing)

    def test_reject_bad_bytecode(self):
        source = 'keep x = 1; sayit(x);'
        original = json.loads(compile_source(source).to_json())
        cases = []
        for index, value in [(0, 999), (0, True), (1, ['not', 'a', 'constant']), (2, -1), (3, 0)]:
            data = json.loads(json.dumps(original))
            data['main']['code'][0][index] = value
            cases.append(data)
        for field, value in [('version', 99), ('format', 'PYTHON'), ('globals', ['__bad']), ('functions', []), ('source', None)]:
            data = json.loads(json.dumps(original))
            data[field] = value
            cases.append(data)
        data = json.loads(json.dumps(original))
        data['main']['code'][0] = [int(Op.JUMP), 999, 1, 1]
        cases.append(data)
        data = json.loads(json.dumps(original))
        data['main']['code'][0] = [int(Op.POP), None, 1, 1]
        cases.append(data)
        data = json.loads(json.dumps(original))
        data['main']['code'][-1] = [int(Op.CALL), ['eval', 0], 1, 1]
        cases.append(data)
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(QwertyError):
                    from_json(json.dumps(data))
        for data in ('', '{}', '[]', 'null', '{"format":'):
            with self.assertRaises(QwertyError):
                from_json(data)

    def test_bytecode_stack_join_validation(self):
        data = json.loads(compile_source('when aye { sayit(1); }').to_json())
        # Replace the initial constant with a jump that enters a POP with no value.
        pop_index = next(i for i, row in enumerate(data['main']['code']) if row[0] == int(Op.POP))
        data['main']['code'][0] = [int(Op.JUMP), pop_index, 1, 1]
        with self.assertRaises(QwertyError):
            from_json(json.dumps(data))


class CLITests(unittest.TestCase):
    def run_cli(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(args)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_run(self):
        status, output, error = self.run_cli(['run', str(ROOT / 'examples' / 'demo.qw')])
        self.assertEqual(status, 0, error)
        self.assertIn('Addition: 25', output)

    def test_check_and_disassemble(self):
        path = str(ROOT / 'examples' / 'demo.qw')
        self.assertEqual(self.run_cli(['check', path])[0], 0)
        self.assertIn('CALL', self.run_cli(['bytecode', path])[1])

    def test_functions(self):
        status, output, error = self.run_cli(['functions'])
        self.assertEqual(status, 0)
        self.assertIn('80 built-in functions', output)

    def test_compile_and_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'compiled.qbc'
            status, _, error = self.run_cli(['compile', str(ROOT / 'examples' / 'demo.qw'), '-o', str(path)])
            self.assertEqual(status, 0, error)
            self.assertTrue(path.exists())
            self.assertIn('Addition: 25', self.run_cli(['run', str(path)])[1])

    def test_missing_file(self):
        self.assertEqual(self.run_cli(['run', str(ROOT / 'not-there.qw')])[0], 2)

    def test_runtime_failure_exit_code(self):
        status, output, error = self.run_cli(['run', str(ROOT / 'examples' / 'error_demo.qw')])
        self.assertEqual(status, 1)
        self.assertIn('Q3002', error)

    def test_compile_cannot_overwrite_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.qw'
            path.write_text('sayit(1);')
            self.assertEqual(self.run_cli(['compile', str(path), '-o', str(path)])[0], 2)
            self.assertEqual(path.read_text(), 'sayit(1);')

    def test_input_file(self):
        status, output, error = self.run_cli(['run', str(ROOT / 'examples' / 'input.qw'), '--input', str(ROOT / 'examples' / 'input.txt')])
        self.assertEqual(status, 0, error)
        self.assertIn('Next year you will be 26', output)


if __name__ == '__main__':
    unittest.main()
