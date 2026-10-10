#!/usr/bin/env python
from tests import unittest
from datetime import datetime, timedelta
import json

import jmespath
from jmespath import exceptions


class TestFunctions(unittest.TestCase):

    def test_can_max_datetimes(self):
        # This is python specific behavior, but JMESPath does not specify what
        # you should do with language specific types.  We're going to add the
        # ability that ``to_string`` will always default to str()'ing values it
        # doesn't understand.
        data = [datetime.now(), datetime.now() + timedelta(seconds=1)]
        result = jmespath.search('max([*].to_string(@))', data)
        self.assertEqual(json.loads(result), str(data[-1]))

    def test_type_error_messages(self):
        with self.assertRaises(exceptions.JMESPathTypeError) as e:
            jmespath.search('length(@)', 2)
        exception = e.exception
        # 1. Function name should be in error message
        self.assertIn('length()', str(exception))
        # 2. Mention it's an invalid type
        self.assertIn('invalid type for value: 2', str(exception))
        # 3. Mention the valid types:
        self.assertIn("expected one of: ['string', 'array', 'object']",
                      str(exception))
        # 4. Mention the actual type.
        self.assertIn('received: "number"', str(exception))

    def test_singular_in_error_message(self):
        with self.assertRaises(exceptions.ArityError) as e:
            jmespath.search('length(@, @)', [0, 1])
        exception = e.exception
        self.assertEqual(
            str(exception),
            'Expected 1 argument for function length(), received 2')

    def test_error_message_is_pluralized(self):
        with self.assertRaises(exceptions.ArityError) as e:
            jmespath.search('sort_by(@)', [0, 1])
        exception = e.exception
        self.assertEqual(
            str(exception),
            'Expected 2 arguments for function sort_by(), received 1')

    def test_variadic_is_pluralized(self):
        with self.assertRaises(exceptions.VariadictArityError) as e:
            jmespath.search('not_null()', 'foo')
        exception = e.exception
        self.assertEqual(
            str(exception),
            'Expected at least 1 argument for function not_null(), received 0')

    def test_contains_array_distinguishes_booleans_from_numbers(self):
        # 2026-10-11: Array membership must use JMESPath scalar equality.
        for value, search in [(True, 1), (False, 0), (1, True), (0, False),
                              (True, 1.0), (False, 0.0)]:
            with self.subTest(value=value, search=search):
                data = {'values': [value], 'search': search}
                self.assertFalse(jmespath.search('contains(values, search)', data))

    def test_contains_array_preserves_valid_matches(self):
        # 2026-10-11: Preserve numeric equivalence and matching JSON types.
        for value, search in [(1, 1.0), (0, 0.0), (True, True),
                              (False, False), (None, None), ('one', 'one')]:
            with self.subTest(value=value, search=search):
                data = {'values': [value], 'search': search}
                self.assertTrue(jmespath.search('contains(values, search)', data))
        self.assertFalse(jmespath.search('contains(@, `true`)', []))
        self.assertTrue(jmespath.search('contains(@, `true`)', [1, True]))
        self.assertTrue(jmespath.search("contains(@, 'bar')", 'foobar'))
