import nodes

EMPTY_TOKEN = ''


class UnknownRegexNodeTypeError(Exception):
    pass


class NFAEdge(object):
    def __init__(self, token=EMPTY_TOKEN, end=None):
        self.token = token
        self.end = end


class NFAState(object):
    def __init__(self, regex_node, e1=None, e2=None):
        # A state in Thompson NFA has at most two forks, we use e1 and e2 to
        # represnet them.
        self.id = None  # Used on conversion to DFA
        self.regex_node = regex_node
        self.e1 = e1
        self.e2 = e2

    def __hash__(self):
        return hash(self.id)

    def traverse(self):
        # yields [(Token, NFAState)]
        for e in (self.e1, self.e2):
            if e:
                yield e.token, e.end

    def __repr__(self):
        return str('NFAState({})'.format(self.id))


class NFA(object):
    def __init__(self, start, end_edges):
        """
        :type self.start: NFAState
        :type self.end_edges: list[NFAEdge]
        :type self.states: list[NFAState]
        :type self.end: NFAState
        """
        self.start = start
        self.end_edges = end_edges
        # The following states will be setup after calling finish()
        self.states = None
        self.end = None

    def link_ends_to(self, state):
        for end in self.end_edges:
            end.end = state

    def finish(self):
        if self.start.id is not None:
            return
        self.end = NFAState(None)
        self.link_ends_to(self.end)
        self.states = self._label_states(self.start)

    @staticmethod
    def _label_states(state):
        current_id = 0
        state.id = current_id
        current_id += 1
        pending_states = [state]
        states = []
        while pending_states:
            state = pending_states.pop()
            states.append(state)
            for _, state1 in state.traverse():
                if state1.id is not None:
                    continue
                state1.id = current_id
                current_id += 1
                pending_states.append(state1)
        return states


def regex_to_nfa(regex_node):
    """
    :type regex_node: nodes.RegexNode
    :rtype: NFA
    """
    if isinstance(regex_node, nodes.Empty):
        state = NFAState(regex_node, NFAEdge())
        return NFA(state, [state.e1])
    elif isinstance(regex_node, nodes.Char):
        state = NFAState(regex_node, NFAEdge(regex_node.token))
        return NFA(state, [state.e1])
    elif isinstance(regex_node, nodes.BinaryRegexNode):
        block1 = regex_to_nfa(regex_node.arg1)
        block2 = regex_to_nfa(regex_node.arg2)
        if isinstance(regex_node, nodes.Concat):
            block1.link_ends_to(block2.start)
            return NFA(block1.start, block2.end_edges)
        elif isinstance(regex_node, nodes.Or):
            state = NFAState(
                regex_node, NFAEdge(end=block1.start), NFAEdge(end=block2.start))
            return NFA(state, block1.end_edges + block2.end_edges)
    elif isinstance(regex_node, nodes.UnaryRegexNode):
        block = regex_to_nfa(regex_node.arg)
        if isinstance(regex_node, nodes.OneOrMore):
            state = NFAState(regex_node, NFAEdge(end=block.start), NFAEdge())
            block.link_ends_to(state)
            return NFA(block.start, [state.e2])
        elif isinstance(regex_node, nodes.ZeroOrMore):
            state = NFAState(regex_node, NFAEdge(end=block.start), NFAEdge())
            block.link_ends_to(state)
            return NFA(state, [state.e2])
        elif isinstance(regex_node, nodes.ZeroOrOne):
            state = NFAState(regex_node, NFAEdge(end=block.start), NFAEdge())
            return NFA(state, block.end_edges + [state.e2])
    raise UnknownRegexNodeTypeError(regex_node)


class TempDFAState(object):
    def __init__(self, nfa_states):
        """
        :type nfa_states: Iterable[NFAState]
        :type self.trans: dict[str, NFAState]
        """
        self.nfa_states = frozenset(find_nfa_closure(nfa_states))
        self.trans = {}
        self.dfa_state = DFAState(self.nfa_states)

    def __hash__(self):
        return hash(self.nfa_states)

    def __eq__(self, rhs):
        return self.nfa_states == rhs.nfa_states

    def add_transition(self, token, state):
        assert token != EMPTY_TOKEN
        try:
            self.trans[token].add(state)
        except KeyError:
            self.trans[token] = {state}

    def get_transitions(self, token, default=frozenset()):
        return self.trans.get(token, default)

    def traverse(self):
        return self.trans.iteritems()

    def __repr__(self):
        return 'TempDFAState(({}))'.format(','.join(str(s.id) for s in self.nfa_states))


class DFAState(object):
    def __init__(self, nfa_states):
        """
        :type nfa_states: Iterable[NFAState]
        """
        self.nfa_states = frozenset(nfa_states)
        """
        :type self.trans: dict[str, DFAState]
        :type self.id: int
        """
        self.trans = {}
        self.is_end = False
        self.is_dead = False
        self.id = None

    def set_transition(self, token, state):
        self.trans[token] = state

    def get_transition(self, token, default=None):
        return self.trans.get(token, default)

    def traverse(self):
        return self.trans.iteritems()

    def __hash__(self):
        return hash(self.nfa_states)

    def __eq__(self, rhs):
        return self.nfa_states == rhs.nfa_states

    def __repr__(self):
        return 'DFAState(({}))'.format(','.join(str(s.id) for s in self.nfa_states))


class DFA(object):
    def __init__(self, states, tokens, start):
        """
        :type states: Iterable[DFAState]
        :type tokens: Iterable[str]
        :type start: DFAState
        """
        self.states = list(states)
        self.tokens = list(tokens)
        self.start = start

    def setup_dead_states(self):
        for state in self.states:
            if not state.is_end and all(s is state for _, s in state.traverse()):
                state.is_dead = True


def find_nfa_closure(nfa_states):
    """
    :type nfa_states: Iterable[NFAState]
    """
    closure = set(nfa_states)
    stack = list(closure)
    while stack:
        s = stack.pop()
        for token, s1 in s.traverse():
            if token == EMPTY_TOKEN and s1 not in closure:
                stack.append(s1)
                closure.add(s1)
    return closure


def nfa_to_dfa(nfa):
    """
    :rtype : DFA
    :type nfa: NFA
    """
    nfa.finish()
    start_tmp_state = TempDFAState({nfa.start})
    pending_dfa_states = [start_tmp_state]
    current_id = 0
    dfa_states = {start_tmp_state: start_tmp_state.dfa_state}
    start_tmp_state.dfa_state.id = current_id
    current_id += 1
    while pending_dfa_states:
        tmp_state = pending_dfa_states.pop()
        for nfa_state in tmp_state.nfa_states:
            for token, nfa_state1 in nfa_state.traverse():
                if token == EMPTY_TOKEN:
                    continue
                tmp_state.add_transition(token, nfa_state1)
        for token, nfa_states in tmp_state.traverse():
            tmp_state1 = TempDFAState(nfa_states)
            if tmp_state1 in dfa_states:
                dfa_state1 = dfa_states[tmp_state1]
            else:
                dfa_state1 = dfa_states[tmp_state1] = tmp_state1.dfa_state
                dfa_state1.id = current_id
                current_id += 1
                pending_dfa_states.append(tmp_state1)
            tmp_state.dfa_state.set_transition(token, dfa_state1)
    # Collect all tokens
    tokens = set()
    for state in dfa_states.itervalues():
        for token, _ in state.traverse():
            tokens.add(token)
    # Create dead state
    tmp_dead_state = TempDFAState([])
    dead_state = tmp_dead_state.dfa_state
    dead_state.id = current_id
    current_id += 1
    # Try to link states to dead state
    has_dead_state = False
    for state in dfa_states.itervalues():
        for token in tokens:
            if state.get_transition(token, dead_state) is dead_state:
                state.set_transition(token, dead_state)
                has_dead_state = True
    # If any state was linked to dead state
    if has_dead_state:
        for token in tokens:
            dead_state.set_transition(token, dead_state)
        dfa_states[tmp_dead_state] = dead_state
    # Create the DFA
    dfa = DFA(dfa_states.itervalues(), tokens, start_tmp_state.dfa_state)
    for state in dfa.states:
        if nfa.end in state.nfa_states:
            state.is_end = True
    dfa.setup_dead_states()
    return dfa


def minimize_dfa(dfa):
    """
    :type dfa: DFA
    :rtype: DFA
    """
    state_to_group = {}
    groups = [[s for s in dfa.states if not s.is_end],
              [s for s in dfa.states if s.is_end]]
    while True:
        for group in groups:
            for state in group:
                state_to_group[state] = group
        new_groups = []
        for group in groups:
            group_id_to_group = {}
            for token in dfa.tokens:
                state_to_new_group = {}
                group_id_to_group = {}
                for state in group:
                    state1 = state.get_transition(token)
                    state_to_new_group[state] = new_group = state_to_group[state1]
                    new_group_id = id(new_group)
                    if new_group_id in group_id_to_group:
                        group_id_to_group[new_group_id].append(state)
                    else:
                        group_id_to_group[new_group_id] = [state]
                if len(group_id_to_group) > 1:
                    break
            new_groups.extend(group_id_to_group.itervalues())
        if len(new_groups) == len(groups):
            break
        groups = new_groups

    group_id_to_new_state = {}
    for group in groups:
        nfa_states = set()
        for dfa_state in group:
            nfa_states.update(dfa_state.nfa_states)
        new_state = DFAState(nfa_states)
        dfa_state = group[0]
        new_state.is_end = dfa_state.is_end
        new_state.is_dead = dfa_state.is_dead
        new_state.id = dfa_state.id
        group_id_to_new_state[id(group)] = new_state
    new_states = []
    for group in groups:
        new_state = group_id_to_new_state[id(group)]
        new_states.append(new_state)
        for token in dfa.tokens:
            next_state = group_id_to_new_state[
                id(state_to_group[group[0].get_transition(token)])]
            new_state.set_transition(token, next_state)
    new_start = group_id_to_new_state[id(state_to_group[dfa.start])]
    # Relabel
    new_states.sort(key=lambda x: x.id)
    for i, new_state in enumerate(new_states):
        new_state.id = i
    return DFA(new_states, dfa.tokens, new_start)
