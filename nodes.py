class RegexNode(object):
    __fields__ = []
    def __repr__(self):
        return '{}({})'.format(
                self.__class__.__name__,
                ','.join(str(getattr(self, field)) for field in self.__fields__))

class Char(RegexNode):
    __fields__ = ['token']
    def __init__(self, token):
        self.token = token

class UnaryRegexNode(RegexNode):
    char = None
    __fields__ = ['arg']
    def __init__(self, arg):
        self.arg = arg

class OneOrMore(UnaryRegexNode):
    char = '+'

class ZeroOrMore(UnaryRegexNode):
    char = '*'

class ZeroOrOne(UnaryRegexNode):
    char = '?'

class BinaryRegexNode(RegexNode):
    __fields__ = ['arg1', 'arg2']
    def __init__(self, arg1, arg2):
        self.arg1 = arg1
        self.arg2 = arg2

class Concat(BinaryRegexNode):
    char = ''

class Or(BinaryRegexNode):
    char = '|'

class Empty(RegexNode):
    pass

UNARY_NODE_TYPES = [OneOrMore, ZeroOrMore, ZeroOrOne]
