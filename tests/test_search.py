import sys
import decimal
from tests import unittest, OrderedDict

import jmespath
import jmespath.functions


class TestSearchOptions(unittest.TestCase):
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


class TestLiteralFreshness(unittest.TestCase):
    """Mutable JSON literals must be re-created on each visit (regression for #318).

    The parser caches the parsed AST per expression, so the literal node
    itself is shared across calls. Without an independent copy, two
    searches of the same literal expression would return the same list/dict
    object, and any in-place mutation by the caller would leak into every
    subsequent search.
    """

    def test_list_literal_is_independent_per_search(self):
        first = jmespath.search('`[]`', {})
        first.extend([1, 2, 3])
        second = jmespath.search('`[]`', {})
        second.extend([9, 8, 7])
        self.assertEqual(first, [1, 2, 3])
        self.assertEqual(second, [9, 8, 7])

    def test_object_literal_is_independent_per_search(self):
        first = jmespath.search('`{}`', {})
        first['x'] = 1
        second = jmespath.search('`{}`', {})
        second['y'] = 2
        self.assertEqual(first, {'x': 1})
        self.assertEqual(second, {'y': 2})

    def test_nested_list_literal_is_independent(self):
        first = jmespath.search('`[[]]`', {})
        first[0].append('a')
        second = jmespath.search('`[[]]`', {})
        second[0].append('b')
        self.assertEqual(first, [['a']])
        self.assertEqual(second, [['b']])

    def test_string_literal_remains_a_string(self):
        # immutable literal should not be wrapped or duplicated
        result = jmespath.search('`"hello"`', {})
        self.assertEqual(result, 'hello')
        self.assertIsInstance(result, str)
