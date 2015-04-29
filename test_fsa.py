import fsa
import parse
import unittest

class TestFSA(unittest.TestCase):
    regexs = [
        "",
        "|",
        "abcd",
        "ab|cd",
        "abc+",
        "abc*",
        "abc?",
        "a(bcd*|efgh?(jk)+)*",
    ]

    def test_regex_to_nfa(self):
        for regex in self.regexs:
            nfa = fsa.regex_to_nfa(parse.from_string(regex))
            nfa.finish()

    def test_nfa_to_dfa(self):
        for regex in self.regexs:
            nfa = fsa.regex_to_nfa(parse.from_string(regex))
            dfa = fsa.nfa_to_dfa(nfa)

    def _get_dfa(self, regex):
        return fsa.nfa_to_dfa(fsa.regex_to_nfa(parse.from_string(regex)))

    def test_dfa(self):
        self.assertGreaterEqual(len(self._get_dfa("abcde").states), 6)
        self.assertGreaterEqual(len(self._get_dfa("ab|de").states), 5)

    def test_minimize_dfa(self):
        dfa = self._get_dfa("(a|b)*aaa(a|b)*")
        mdfa = fsa.minimize_dfa(dfa)

if __name__ == '__main__':
    unittest.main()
