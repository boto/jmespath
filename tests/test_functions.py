#!/usr/bin/env python
from tests import unittest
from datetime import datetime, timedelta
import json

import jmespath
from jmespath import exceptions


class TestFunctions(unittest.TestCase):

    def test_extrema_reject_mixed_key_types(self):
        for function in ('min_by', 'max_by'):
            for keys, expected_type, actual_type in (
                    ([1, '2'], 'number', 'string'),
                    (['1', 2], 'string', 'number')):
                with self.subTest(function=function, keys=keys):
                    data = [{'key': key} for key in keys]
                    with self.assertRaises(exceptions.JMESPathTypeError) as e:
                        jmespath.search('%s(@, &key)' % function, data)
                    self.assertEqual(e.exception.function_name, function)
                    self.assertEqual(e.exception.current_value, keys[1])
                    self.assertEqual(e.exception.actual_type, actual_type)
                    self.assertEqual(e.exception.expected_types, [expected_type])

    def test_extrema_accept_integer_and_float_keys(self):
        data = [{'key': 2}, {'key': 1.5}, {'key': 3.5}]
        self.assertEqual(jmespath.search('min_by(@, &key)', data), data[1])
        self.assertEqual(jmespath.search('max_by(@, &key)', data), data[2])

    def test_extrema_key_type_is_local_to_each_search(self):
        for function in ('min_by', 'max_by'):
            with self.subTest(function=function):
                expression = jmespath.compile('%s(@, &key)' % function)
                for key in (1, 'a'):
                    data = [{'key': key}]
                    self.assertEqual(expression.search(data), data[0])

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
