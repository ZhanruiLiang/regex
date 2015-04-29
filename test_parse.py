import unittest
import parse
import nodes as N


class TestParse(unittest.TestCase):
    def _compare(self, regex, expected):
        self.assertEqual(repr(parse.from_string(regex)), repr(expected))

    def test_concat(self):
        self._compare('abc', N.Concat(N.Concat(N.Char('a'), N.Char('b')), N.Char('c')))
        self._compare('abcde',
                N.Concat(
                    N.Concat(
                        N.Concat(
                            N.Concat(N.Char('a'), N.Char('b')),
                            N.Char('c')),
                        N.Char('d')),
                    N.Char('e')))

    def test_or(self):
        self._compare('a|b', N.Or(N.Char('a'), N.Char('b')))
        self._compare('ab|c', N.Or(N.Concat(N.Char('a'), N.Char('b')), N.Char('c')))
        self._compare('a|bc', N.Or(N.Char('a'), N.Concat(N.Char('b'), N.Char('c'))))
        self._compare('a|b|c', N.Or(N.Or(N.Char('a'), N.Char('b')), N.Char('c')))
        self._compare('|', N.Or(N.Empty(), N.Empty()))

    def test_unary(self):
        self._compare('a?', N.ZeroOrOne(N.Char('a')))
        self._compare('ab+', N.Concat(N.Char('a'), N.OneOrMore(N.Char('b'))))
        self._compare('a+b', N.Concat(N.OneOrMore(N.Char('a')), N.Char('b')))

    def test_unary_multiple(self):
        self._compare('a+?', N.ZeroOrOne(N.OneOrMore(N.Char('a'))))
        self._compare('a+++', N.OneOrMore(N.OneOrMore(N.OneOrMore(N.Char('a')))))

    def test_empty(self):
        self._compare('', N.Empty())
        self._compare('a|', N.Or(N.Char('a'), N.Empty()))
        self._compare('|a', N.Or(N.Empty(), N.Char('a')))

    def test_parentheses(self):
        self._compare('()', N.Empty())
        self._compare('(ab)+', N.OneOrMore(N.Concat(N.Char('a'), N.Char('b'))))
        self._compare('a(b)+', N.Concat(N.Char('a'), N.OneOrMore(N.Char('b'))))
        parse.from_string('a(bcd*|efgh?(jk)+)*')


if __name__ == '__main__':
    unittest.main()
