import nodes

class ParseState(object):
    NO_OPR = 0
    UNARY = 1
    BINARY = 2

    def __init__(self):
        self.level = 0
        self.state = self.NO_OPR
        self.opr_type = None
        self.opr_index = None


def from_string(regex):
    # regex: str -> node: RegexNode
    if not regex:
        return nodes.Empty()
    state = ParseState()
    for i, c in enumerate(regex):
        if state.level == 0:
            if any(type_.char == c for type_ in nodes.UNARY_NODE_TYPES):
                if state.state != ParseState.BINARY:
                    state.state = ParseState.UNARY
                    state.opr_type = next(t for t in nodes.UNARY_NODE_TYPES if t.char == c)
                    state.opr_index = i
            elif c == nodes.Or.char:
                state.opr_type = nodes.Or
                state.opr_index = i
                state.state = ParseState.BINARY
            elif state.state != ParseState.BINARY or state.opr_type != nodes.Or:
                if i > 0:
                    state.state = ParseState.BINARY
                    state.opr_type = nodes.Concat
                    state.opr_index = i
        if c == '(':
            state.level += 1
        elif c == ')':
            state.level -= 1

    if state.state == ParseState.NO_OPR:
        if regex[0] == '(' and regex[-1] == ')':
            return from_string(regex[1:-1])
        assert len(regex) == 1, 'Unexpected regex: {}'.format(regex)
        return nodes.Char(regex)
    elif state.state == ParseState.UNARY:
        assert state.opr_index == len(regex) - 1, 'Invalid sub-regex: {}'.format(regex)
        return state.opr_type(from_string(regex[:state.opr_index]))
    elif state.state == ParseState.BINARY:
        return state.opr_type(
                from_string(regex[:state.opr_index]),
                from_string(regex[state.opr_index + len(state.opr_type.char):]))
    else:
        raise Exception('Unknown state: {}'.format(state.state))
