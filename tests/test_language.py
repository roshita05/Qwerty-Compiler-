from __future__ import annotations
import builtins as python_builtins
import random
import unittest
from qwerty import Limits, QwertyError, compile_source, execute
from qwerty.builtins import REGISTRY


class BuiltinTests(unittest.TestCase):
    def test_exactly_80_custom_names(self):
        self.assertEqual(len(REGISTRY), 80)
        self.assertFalse(set(REGISTRY).intersection(dir(python_builtins)))
        self.assertTrue(all(name.endswith('it') for name in REGISTRY))


def builtin_test(builtin):
    def test(self):
        result = execute('keep result = ' + builtin.example + ';', inputs=['Ada'])
        self.assertEqual(result.globals['result'], builtin.expected)
        self.assertIs(type(result.globals['result']), type(builtin.expected))
    return test


def arity_test(builtin):
    def test(self):
        count = builtin.minimum - 1 if builtin.minimum else builtin.maximum + 1
        source = f'{builtin.name}(' + ','.join('1' for _ in range(count)) + ');'
        with self.assertRaises(QwertyError):
            compile_source(source)
    return test


for name, builtin in REGISTRY.items():
    setattr(BuiltinTests, 'test_example_' + name, builtin_test(builtin))
    setattr(BuiltinTests, 'test_wrong_arity_' + name, arity_test(builtin))


class LanguageTests(unittest.TestCase):
    def value(self, expression):
        return execute('keep result = ' + expression + ';').globals['result']

    def test_arithmetic_precedence(self):
        self.assertEqual(self.value('2 + 3 * 4'), 14)
        self.assertEqual(self.value('(2 + 3) * 4'), 20)
        self.assertEqual(self.value('2 ** 3 ** 2'), 512)
        self.assertEqual(self.value('-2 ** 2'), -4)
        self.assertEqual(self.value('2 ** -2'), 0.25)
        self.assertEqual(self.value('9 // 2'), 4)

    def test_boolean_spellings(self):
        self.assertEqual(execute('sayit(aye, nay, void);').output, 'aye nay void\n')

    def test_boolean_values_are_not_numbers(self):
        self.assertIs(self.value('equalit(aye, 1)'), False)
        self.assertIs(self.value('equalit([aye], [1])'), False)
        self.assertIs(self.value('equalit(mapit(["a"], [aye]), mapit(["a"], [1]))'), False)
        with self.assertRaises(QwertyError):
            self.value('addit(aye, 1)')

    def test_short_circuit(self):
        self.assertIs(self.value('nay && divit(1, 0)'), False)
        self.assertIs(self.value('aye || divit(1, 0)'), True)
        self.assertIs(self.value('1 && 2'), True)
        self.assertIs(self.value('0 || "yes"'), True)

    def test_logical_builtins_are_eager(self):
        with self.assertRaises(QwertyError):
            self.value('andit(nay, divit(1, 0))')

    def test_if_else_if(self):
        source = 'keep n = 2; when n == 1 { sayit("one"); } otherwise when n == 2 { sayit("two"); } otherwise { sayit("other"); }'
        self.assertEqual(execute(source).output, 'two\n')

    def test_while_break_continue(self):
        result = execute('keep n = 0; whilst n < 8 { n = n + 1; when n == 2 { skip; } when n == 5 { stop; } sayit(n); }')
        self.assertEqual(result.output, '1\n3\n4\n')

    def test_each_nested_and_break(self):
        result = execute('each a over [1, 2] { each b over [3, 4, 5] { when b == 4 { stop; } sayit(a, b); } }')
        self.assertEqual(result.output, '1 3\n2 3\n')

    def test_each_continue(self):
        self.assertEqual(execute('each n over [1, 2, 3] { when n == 2 { skip; } sayit(n); }').output, '1\n3\n')

    def test_each_text_and_map(self):
        self.assertEqual(execute('each c over "hi" { sayit(c); } each k over mapit(["a"], [1]) { sayit(k); }').output, 'h\ni\na\n')

    def test_empty_iteration(self):
        self.assertEqual(execute('each x over [] { sayit(x); } sayit("done");').output, 'done\n')

    def test_scope_shadowing(self):
        self.assertEqual(execute('keep x = 1; { keep x = 2; sayit(x); } sayit(x);').output, '2\n1\n')

    def test_shadow_initializer_reads_outer(self):
        self.assertEqual(execute('keep x = 3; { keep x = addit(x, 1); sayit(x); }').output, '4\n')

    def test_lexical_not_dynamic_scope(self):
        result = execute('keep x = 10; craft readx() { give x; } craft caller() { keep x = 20; give readx(); } sayit(caller());')
        self.assertEqual(result.output, '10\n')

    def test_function_forward_calls(self):
        self.assertEqual(execute('sayit(twice(4)); craft twice(x) { give multit(x, 2); }').output, '8\n')

    def test_recursion(self):
        source = 'craft fact(n) { when n <= 1 { give 1; } give n * fact(n - 1); } sayit(fact(6));'
        self.assertEqual(execute(source).output, '720\n')

    def test_mutual_recursion(self):
        source = 'craft evenq(n) { when n == 0 { give aye; } give oddq(n-1); } craft oddq(n) { when n == 0 { give nay; } give evenq(n-1); } sayit(evenq(10));'
        self.assertEqual(execute(source).output, 'aye\n')

    def test_global_update(self):
        result = execute('keep n = 0; craft bump() { n = addit(n, 1); } bump(); bump(); sayit(n);')
        self.assertEqual(result.output, '2\n')

    def test_return_in_loop(self):
        source = 'craft firstq(xs) { each x over xs { give x; } give void; } sayit(firstq([9, 8]));'
        self.assertEqual(execute(source).output, '9\n')

    def test_empty_and_implicit_return(self):
        self.assertEqual(execute('craft f() {} craft g() { give; } sayit(f(), g());').output, 'void void\n')

    def test_zero_arg_functions_and_empty_lists(self):
        self.assertEqual(self.value('listit()'), [])
        self.assertEqual(self.value('concatit()'), '')
        self.assertEqual(self.value('mapit([], [])'), {})
        self.assertEqual(execute('sayit();').output, '\n')

    def test_negative_indices_and_slice(self):
        self.assertEqual(self.value('[10, 20, 30][-1]'), 30)
        self.assertEqual(self.value('"hello"[1]'), 'e')
        self.assertEqual(self.value('sliceit([1, 2, 3, 4], -3, -1)'), [2, 3])

    def test_collection_updates_are_immutable(self):
        result = execute('keep a = [1, 2]; keep b = pushit(a, 3); keep c = putit(a, 0, 9); keep m = mapit(["a"], [1]); keep n = setit(m, "a", 2);')
        self.assertEqual(result.globals['a'], [1, 2])
        self.assertEqual(result.globals['b'], [1, 2, 3])
        self.assertEqual(result.globals['c'], [9, 2])
        self.assertEqual(result.globals['m'], {'a': 1})
        self.assertEqual(result.globals['n'], {'a': 2})

    def test_map_defaults_and_duplicate_keys(self):
        self.assertEqual(self.value('getit(mapit([], []), "absent", 42)'), 42)
        self.assertIsNone(self.value('getit(mapit([], []), "absent")'))
        self.assertEqual(self.value('mapit(["a", "a"], [1, 2])'), {'a': 2})

    def test_span_variants(self):
        self.assertEqual(self.value('spanit(3)'), [0, 1, 2])
        self.assertEqual(self.value('spanit(2, 5)'), [2, 3, 4])
        self.assertEqual(self.value('spanit(5, 0, -2)'), [5, 3, 1])

    def test_sort_descending(self):
        self.assertEqual(self.value('sortit([1, 3, 2], aye)'), [3, 2, 1])
        self.assertEqual(self.value('sortit(["z", "a"])'), ['a', 'z'])

    def test_unique_nested_and_boolean(self):
        self.assertEqual(self.value('uniqueit([[1], [1], [2]])'), [[1], [2]])
        result = self.value('uniqueit([aye, 1, 1.0])')
        self.assertEqual(len(result), 2)
        self.assertIs(result[0], True)
        self.assertIs(type(result[1]), int)

    def test_strings_comments_and_unicode(self):
        source = '# Line comment\n/* two\nlines */\nsayit("hi\\nthere", "\\u0041", \'quote\\\'s\');'
        self.assertEqual(execute(source).output, "hi\nthere A quote's\n")
        self.assertEqual(self.value('"caf\u00e9"'), 'caf\u00e9')
        self.assertEqual(self.value('charit(128512)'), '\U0001f600')

    def test_exponential_numbers(self):
        self.assertEqual(self.value('1.5e2 + 2E-1'), 150.2)

    def test_truthiness(self):
        for expression in ('0', '0.0', '""', '[]', 'void', 'mapit([], [])'):
            self.assertIs(self.value(f'boolit({expression})'), False)
        self.assertIs(self.value('boolit("nay")'), True)

    def test_input_queue_and_prompt(self):
        result = execute('keep name = askit("Name: "); sayit(name);', inputs=['Ada'])
        self.assertEqual(result.output, 'Name: Ada\n')

    def test_input_callback(self):
        result = execute('sayit(askit());', input_reader=lambda: 'callback')
        self.assertEqual(result.output, 'callback\n')

    def test_output_callback(self):
        output = []
        result = execute('sayit(1); sayit(2);', output_sink=output.append)
        self.assertEqual(''.join(output), result.output)

    def test_empty_program(self):
        self.assertEqual(execute('').output, '')

    def test_isolated_runs(self):
        execute('keep secret = 42;')
        with self.assertRaises(QwertyError):
            execute('sayit(secret);')

    def test_compile_does_not_execute(self):
        compile_source('sayit(divit(1, 0));')

    def test_randomized_numeric_expressions(self):
        rng = random.Random(42)
        for _ in range(100):
            a, b, c = [rng.randint(-100, 100) for _ in range(3)]
            self.assertEqual(self.value(f'({a}) + ({b}) * ({c})'), a + b * c)


BAD_CASES = {
    'missing_semicolon': ('keep a = 1', 'SyntaxError'),
    'missing_brace': ('when aye { sayit(1);', 'SyntaxError'),
    'missing_paren': ('sayit(1;', 'SyntaxError'),
    'unterminated_string': ('sayit("hello);', 'LexicalError'),
    'bad_escape': ('sayit("\\q");', 'LexicalError'),
    'bad_unicode': ('sayit("\\uZZZZ");', 'LexicalError'),
    'surrogate': ('sayit("\\uD800");', 'LexicalError'),
    'unterminated_comment': ('/* hello', 'LexicalError'),
    'invalid_character': ('sayit(@);', 'LexicalError'),
    'unknown_variable': ('sayit(missing);', 'CompileError'),
    'unknown_function': ('add(1, 2);', 'CompileError'),
    'python_print': ('print(1);', 'CompileError'),
    'python_import': ('import os;', 'SyntaxError'),
    'python_dunder': ('__import__("os");', 'LexicalError'),
    'python_attribute': ('keep x = 1; x.__class__;', 'LexicalError'),
    'duplicate_variable': ('keep x = 1; keep x = 2;', 'CompileError'),
    'duplicate_function': ('craft f() {} craft f() {}', 'CompileError'),
    'duplicate_parameter': ('craft f(x,x) {}', 'CompileError'),
    'parameter_builtin': ('craft f(addit) {}', 'CompileError'),
    'parameter_function': ('craft f(f) {}', 'CompileError'),
    'builtin_redefinition': ('craft addit(x,y) {}', 'CompileError'),
    'builtin_variable': ('keep addit = 1;', 'CompileError'),
    'nested_function': ('craft f() { craft g() {} }', 'CompileError'),
    'nested_conditional_function': ('when aye { craft f() {} }', 'CompileError'),
    'outside_break': ('stop;', 'CompileError'),
    'outside_continue': ('skip;', 'CompileError'),
    'outside_return': ('give 1;', 'CompileError'),
    'block_local_escape': ('{ keep x = 1; } sayit(x);', 'CompileError'),
    'loop_local_escape': ('each x over [1] {} sayit(x);', 'CompileError'),
    'uninitialized_global': ('f(); keep x = 1; craft f() { sayit(x); }', 'RuntimeError'),
    'uninitialized_global_write': ('f(); keep x = 1; craft f() { x = 2; }', 'RuntimeError'),
    'forward_variable': ('sayit(x); keep x = 1;', 'CompileError'),
    'self_initializer': ('keep x = x;', 'CompileError'),
    'zero_division': ('divit(1,0);', 'RuntimeError'),
    'zero_remainder': ('modit(1,0);', 'RuntimeError'),
    'wrong_type': ('addit("x", 2);', 'TypeError'),
    'wrong_index_type': ('pickit([1], aye);', 'TypeError'),
    'empty_index': ('firstit([]);', 'IndexError'),
    'bad_index': ('pickit([1], 9);', 'IndexError'),
    'indexed_assignment': ('keep xs = [1]; xs[0] = 2;', 'SyntaxError'),
    'bad_root': ('rootit(-1);', 'RuntimeError'),
    'bad_factorial': ('factorit(-1);', 'RuntimeError'),
    'bad_integer': ('intit("abc");', 'RuntimeError'),
    'nonfinite_float': ('floatit("nan");', 'RuntimeError'),
    'nonfinite_literal': ('sayit(1e999);', 'LexicalError'),
    'empty_min': ('minit([]);', 'RuntimeError'),
    'empty_average': ('avgit([]);', 'RuntimeError'),
    'empty_pop': ('popit([]);', 'IndexError'),
    'remove_missing': ('removeit([1], 2);', 'RuntimeError'),
    'empty_separator': ('splitit("abc", "");', 'RuntimeError'),
    'mixed_sort': ('sortit([1, "x"]);', 'TypeError'),
    'zero_range_step': ('spanit(1, 4, 0);', 'RuntimeError'),
    'bad_map_keys': ('mapit([1], [2]);', 'TypeError'),
    'unequal_map_lists': ('mapit(["a"], []);', 'RuntimeError'),
    'noniterable_each': ('each x over 3 {}', 'TypeError'),
    'failed_assertion': ('assertit(nay, "Expected failure");', 'AssertionError'),
    'missing_input': ('askit();', 'InputError'),
    'negative_repeat': ('repeatit("a", -1);', 'RuntimeError'),
    'huge_repeat': ('repeatit("a", 100001);', 'LimitError'),
    'huge_range': ('spanit(10001);', 'LimitError'),
    'huge_exponent': ('powerit(2, 1000000);', 'LimitError'),
    'complex_power': ('powerit(-1, 0.5);', 'RuntimeError'),
    'bad_char': ('charit(55296);', 'RuntimeError'),
    'bad_code': ('codeit("ab");', 'RuntimeError'),
    'bad_clamp': ('clampit(5, 10, 0);', 'RuntimeError'),
    'bad_order': ('lessit(aye, 1);', 'TypeError'),
}


class DiagnosticTests(unittest.TestCase):
    def test_line_column_and_hint(self):
        with self.assertRaises(QwertyError) as caught:
            execute('keep x = 0;\nsayit(divit(1, x));', filename='test.qw')
        error = caught.exception
        self.assertEqual((error.location.line, error.location.column), (2, 7))
        self.assertIn('test.qw:2:7', str(error))
        self.assertIn('Hint:', str(error))
        self.assertIn('^', str(error))

    def test_carriage_return_line_locations(self):
        with self.assertRaises(QwertyError) as caught:
            execute('keep x = 0;\rsayit(divit(1, x));')
        self.assertEqual(caught.exception.location.line, 2)

    def test_custom_name_hint(self):
        with self.assertRaises(QwertyError) as caught:
            compile_source('subtract(4, 2);')
        self.assertIn('subit', caught.exception.hint)

    def test_call_stack(self):
        with self.assertRaises(QwertyError) as caught:
            execute('craft f() { give divit(1,0); } craft g() { give f(); } g();')
        self.assertEqual(caught.exception.trace, ['f', 'g', '<main>'])

    def test_partial_output(self):
        with self.assertRaises(QwertyError) as caught:
            execute('sayit("before"); divit(1,0);')
        self.assertEqual(caught.exception.output, 'before\n')

    def test_step_budget(self):
        with self.assertRaises(QwertyError) as caught:
            execute('whilst aye {}', limits=Limits(max_steps=30))
        self.assertEqual(caught.exception.code, 'Q4012')

    def test_call_depth_budget(self):
        with self.assertRaises(QwertyError) as caught:
            execute('craft f() { give f(); } f();', limits=Limits(max_call_depth=5))
        self.assertEqual(caught.exception.code, 'Q4013')

    def test_output_budget(self):
        with self.assertRaises(QwertyError):
            execute('sayit("abcdef");', limits=Limits(max_output=5))

    def test_source_budget(self):
        with self.assertRaises(QwertyError):
            compile_source(' ' * 100001)

    def test_nesting_budget(self):
        with self.assertRaises(QwertyError):
            compile_source('sayit(' + '(' * 100 + '1' + ')' * 100 + ');')

    def test_shared_graph_render_budget(self):
        source = 'keep x = [0]; each i over spanit(24) { x = [x, x]; } sayit(x);'
        with self.assertRaises(QwertyError) as caught:
            execute(source)
        self.assertEqual(caught.exception.kind, 'LimitError')

    def test_fuzz_invalid_source_no_python_traceback(self):
        rng = random.Random(2026)
        alphabet = 'abc0123{}[]();=+-*/!#\n\"\' '
        for _ in range(300):
            source = ''.join(rng.choice(alphabet) for _ in range(rng.randrange(1, 80)))
            try:
                execute(source, limits=Limits(max_steps=1000))
            except QwertyError:
                pass


def diagnostic_test(source, category):
    def test(self):
        with self.assertRaises(QwertyError) as caught:
            execute(source)
        self.assertEqual(caught.exception.kind, category, str(caught.exception))
    return test


for name, (source, category) in BAD_CASES.items():
    setattr(DiagnosticTests, 'test_error_' + name, diagnostic_test(source, category))


if __name__ == '__main__':
    unittest.main()
