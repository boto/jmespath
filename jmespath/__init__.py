from jmespath import parser
from jmespath.visitor import Options

__version__ = '1.1.0'


def compile(expression, options=None):
    parsed = parser.Parser().parse(expression)
    if options is None:
        return parsed
    return parser.ParsedResult(parsed.expression, parsed.parsed, options=options)


def search(expression, data, options=None):
    return parser.Parser().parse(expression).search(data, options=options)
