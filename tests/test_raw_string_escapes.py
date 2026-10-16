from tests import unittest

import jmespath
from jmespath.lexer import Lexer


class TestRawStringEscapes(unittest.TestCase):

    def test_escaped_backslash_is_unescaped(self):
        tokens = list(Lexer().tokenize(r"'\\'"))
        self.assertEqual(tokens[0]['value'], '\\')
        self.assertEqual(jmespath.search(r"'\\'", {}), '\\')

    def test_backslash_before_other_character_is_preserved(self):
        self.assertEqual(jmespath.search(r"'\z'", {}), r'\z')

    def test_escaped_quote_is_unescaped(self):
        self.assertEqual(jmespath.search(r"'foo\'bar'", {}), "foo'bar")

    def test_windows_path_filter_with_trailing_backslash(self):
        rows = [{'FullName': r'C:\x\msvc\file.txt'}]
        expression = r"[? !contains(FullName, '\msvc\\')]"
        self.assertEqual(jmespath.search(expression, rows), [])
