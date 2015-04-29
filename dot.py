import fsa


class DotNode(object):
    def __init__(self, **attrs):
        self.attrs = attrs
        self.id = None


class DotEdge(object):
    def __init__(self, node1, node2, **attrs):
        self.node1 = node1
        self.node2 = node2
        self.attrs = attrs


class DotGraph(object):
    def __init__(self, title=""):
        """
        :type title: str
        :type self.nodes: dict[str, DotNode]
        :type self.edges: list[DotEdge]
        """
        self.title = title
        self.nodes = {}
        self.edges = []
        self._current_id = 0

    def add_node(self, *args, **kwargs):
        """:rtype: DotNode"""
        node = DotNode(*args, **kwargs)
        node.id = self._current_id
        self._current_id += 1
        self.nodes[node.id] = node
        return node

    def add_edge(self, *args, **kwargs):
        """:rtype: DotEdge"""
        edge = DotEdge(*args, **kwargs)
        self.edges.append(edge)
        return edge

    def format(self):
        lines = [
            'digraph {',
            '  rankdir=LR',
        ]
        for node in self.nodes.itervalues():
            lines.append('  S{}[{}]'.format(
                node.id, self._format_attrs(node.attrs)))
        for edge in self.edges:
            lines.append('  S{}->S{}[{}]'.format(
                edge.node1.id, edge.node2.id, self._format_attrs(edge.attrs)))
        lines.append('}')
        return '\n'.join(lines)

    @staticmethod
    def _format_attrs(attrs):
        return ','.join('{}="{}"'.format(k, v) for k, v in attrs.iteritems())

    def save(self, path):
        open(path, 'w').write(self.format())


def nfa_to_dot(nfa):
    """
    :type nfa: fsa.NFA
    :rtype: DotGraph
    """
    nfa.finish()
    dot = DotGraph("NFA")
    empty = dot.add_node(label="", shape="none")
    nodes = {}
    for state in nfa.states:
        shape = "circle" if state != nfa.end else "doublecircle"
        nodes[state] = dot.add_node(label=str(state.id), shape=shape)
    dot.add_edge(empty, nodes[nfa.start])
    for state in nfa.states:
        for token, state1 in state.traverse():
            dot.add_edge(nodes[state], nodes[state1], label=token)
    return dot


def dfa_to_dot(dfa, details=False, show_deads=True):
    """
    :type dfa: fsa.DFA
    :rtype: DotGraph
    """
    dot = DotGraph("DFA")
    empty = dot.add_node(label="", shape="none")
    nodes = {}
    for state in dfa.states:
        if not show_deads and state.is_dead:
            continue
        shape = "circle" if not state.is_end else "doublecircle"
        label = ','.join(str(x.id) for x in state.nfa_states) if details else str(state.id)
        nodes[state] = dot.add_node(label=label, shape=shape)
    dot.add_edge(empty, nodes[dfa.start])
    for state in dfa.states:
        for token, state1 in state.traverse():
            if not show_deads and (state.is_dead or state1.is_dead):
                continue
            dot.add_edge(nodes[state], nodes[state1], label=token)
    return dot


def main():
    import sys
    import parse

    HELP_MESSAGE = """
Usage:
  python dot.py (nfa|dfa|mdfa) REGEX

Here mdfa stands for minimized DFA.

For example:
  python dot.py mdfa "a*(a|b)b*" | dot -Tpng -o /tmp/dot.png && open /tmp/dot.png
  """.strip()
    try:
        type_, regex = sys.argv[1:]
    except:
        exit(HELP_MESSAGE)

    if type_ == 'nfa':
        nfa = fsa.regex_to_nfa(parse.from_string(regex))
        dot = nfa_to_dot(nfa)
    elif type_ == 'dfa':
        nfa = fsa.regex_to_nfa(parse.from_string(regex))
        dfa = fsa.nfa_to_dfa(nfa)
        dot = dfa_to_dot(dfa)
    elif type_ == 'mdfa':
        nfa = fsa.regex_to_nfa(parse.from_string(regex))
        dfa = fsa.nfa_to_dfa(nfa)
        mdfa = fsa.minimize_dfa(dfa)
        dot = dfa_to_dot(mdfa)
    else:
        raise Exception("Unknown type: {}".format(type_))
    print dot.format()


if __name__ == '__main__':
    main()
