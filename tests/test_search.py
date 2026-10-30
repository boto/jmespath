import sys
import decimal
from tests import unittest, OrderedDict

import jmespath
import jmespath.functions


class TestSearchOptions(unittest.TestCase):
    def test_compile_uses_default_options(self):
        expression = jmespath.compile(
            '{a: a, b: b}',
            options=jmespath.Options(dict_cls=OrderedDict))
        result = expression.search({'a': 1, 'b': 2})
        self.assertIsInstance(result, OrderedDict)
        self.assertEqual(list(result.items()), [('a', 1), ('b', 2)])

    def test_search_options_override_compiled_defaults(self):
        expression = jmespath.compile(
            '{a: a}', options=jmespath.Options(dict_cls=OrderedDict))
        result = expression.search(
            {'a': 1}, options=jmespath.Options(dict_cls=dict))
        self.assertIs(type(result), dict)
        self.assertIsInstance(expression.search({'a': 2}), OrderedDict)

    def test_compiled_defaults_do_not_leak_between_expressions(self):
        class OtherDict(dict):
            pass

        plain = jmespath.compile('{a: a}')
        ordered = jmespath.compile(
            '{a: a}', options=jmespath.Options(dict_cls=OrderedDict))
        other = jmespath.compile(
            '{a: a}', options=jmespath.Options(dict_cls=OtherDict))
        self.assertIsInstance(ordered.search({'a': 1}), OrderedDict)
        self.assertIsInstance(other.search({'a': 1}), OtherDict)
        self.assertIs(type(plain.search({'a': 1})), dict)
        self.assertIs(type(jmespath.compile('{a: a}').search({'a': 1})), dict)
        self.assertIs(type(jmespath.search('{a: a}', {'a': 1})), dict)

    def test_compile_with_custom_functions(self):
        class CustomFunctions(jmespath.functions.Functions):
            @jmespath.functions.signature({'types': ['number']})
            def _func_double(self, number):
                return number * 2

        expression = jmespath.compile(
            'double(value)',
            options=jmespath.Options(custom_functions=CustomFunctions()))
        self.assertEqual(expression.search({'value': 3}), 6)
        self.assertEqual(expression.search({'value': 5}), 10)
        with self.assertRaises(jmespath.exceptions.UnknownFunctionError):
            jmespath.search('double(value)', {'value': 3})

    def test_can_provide_dict_cls(self):
        result = jmespath.search(
            '{a: a, b: b, c: c}.*',
            {'c': 'c', 'b': 'b', 'a': 'a', 'd': 'd'},
            options=jmespath.Options(dict_cls=OrderedDict))
        self.assertEqual(result, ['a', 'b', 'c'])

    def test_can_provide_custom_functions(self):
        class CustomFunctions(jmespath.functions.Functions):
            @jmespath.functions.signature(
                {'types': ['number']},
                {'types': ['number']})
            def _func_custom_add(self, x, y):
                return x + y

            @jmespath.functions.signature(
                {'types': ['number']},
                {'types': ['number']})
            def _func_my_subtract(self, x, y):
                return x - y


        options = jmespath.Options(custom_functions=CustomFunctions())
        self.assertEqual(
            jmespath.search('custom_add(`1`, `2`)', {}, options=options),
            3
        )
        self.assertEqual(
            jmespath.search('my_subtract(`10`, `3`)', {}, options=options),
            7
        )
        # Should still be able to use the original functions without
        # any interference from the CustomFunctions class.
        self.assertEqual(
            jmespath.search('length(`[1, 2]`)', {}), 2
        )



class TestPythonSpecificCases(unittest.TestCase):
    def test_can_compare_strings(self):
        # This is python specific behavior that's not in the official spec
        # yet, but this was regression from 0.9.0 so it's been added back.
        self.assertTrue(jmespath.search('a < b', {'a': '2016', 'b': '2017'}))

    @unittest.skipIf(not hasattr(sys, 'maxint'), 'Test requires long() type')
    def test_can_handle_long_ints(self):
        result = sys.maxint + 1
        self.assertEqual(jmespath.search('[?a >= `1`].a', [{'a': result}]),
                         [result])

    def test_can_handle_decimals_as_numeric_type(self):
        result = decimal.Decimal('3')
        self.assertEqual(jmespath.search('[?a >= `1`].a', [{'a': result}]),
                         [result])
