"""LR(0) items, closure, goto, and SLR(1) parsing table construction."""

from __future__ import annotations

from dataclasses import dataclass

from tmlc.parser.first_follow import compute_first, compute_follow
from tmlc.parser.grammar import Grammar


@dataclass(frozen=True)
class LR0Item:
    """An LR(0) item representing a production with a position marker (dot).

    Attributes:
        prod_id: Identifier of the production in grammar.productions.
        dot: 0-based index of the symbol following the dot.
    """

    prod_id: int
    dot: int

    def next_symbol(self, grammar: Grammar) -> str | None:
        """Return the grammar symbol immediately following the dot, or None if at the end."""
        prod = grammar.productions[self.prod_id]
        if self.dot < len(prod.body):
            return prod.body[self.dot]
        return None

    def advance(self) -> LR0Item:
        """Return a new LR0Item with the dot moved one symbol to the right."""
        return LR0Item(self.prod_id, self.dot + 1)

    def is_kernel(self) -> bool:
        """True if the item is a kernel item (dot > 0 or augmented start production)."""
        return self.dot > 0 or self.prod_id == 0

    def format(self, grammar: Grammar) -> str:
        """Format item for debug printing (e.g. 'Model -> MODEL . IDENT LBRACE ...')."""
        prod = grammar.productions[self.prod_id]
        body_with_dot = list(prod.body)
        body_with_dot.insert(self.dot, "•")
        return f"{prod.head} -> {' '.join(body_with_dot)}"


def lr0_closure(items: frozenset[LR0Item], grammar: Grammar) -> frozenset[LR0Item]:
    """Compute the LR(0) closure of a set of items."""
    closure_set = set(items)
    changed = True

    while changed:
        changed = False
        new_items: set[LR0Item] = set()
        for item in closure_set:
            sym = item.next_symbol(grammar)
            if sym is not None and sym in grammar.nonterminals:
                for prod in grammar.productions_for(sym):
                    candidate = LR0Item(prod.id, 0)
                    if candidate not in closure_set:
                        new_items.add(candidate)
                        changed = True
        closure_set.update(new_items)

    return frozenset(closure_set)


def lr0_goto(
    items: frozenset[LR0Item], symbol: str, grammar: Grammar
) -> frozenset[LR0Item]:
    """Compute GOTO(I, X) transition for an item set and grammar symbol."""
    moved: set[LR0Item] = set()
    for item in items:
        if item.next_symbol(grammar) == symbol:
            moved.add(item.advance())
    return lr0_closure(frozenset(moved), grammar)


def build_lr0_automaton(grammar: Grammar) -> list[frozenset[LR0Item]]:
    """Build canonical collection of LR(0) item sets (states)."""
    initial_item = LR0Item(0, 0)  # Start -> • Model
    initial_state = lr0_closure(frozenset([initial_item]), grammar)

    states: list[frozenset[LR0Item]] = [initial_state]
    state_indices: dict[frozenset[LR0Item], int] = {initial_state: 0}

    all_symbols = sorted(grammar.terminals | grammar.nonterminals)

    idx = 0
    while idx < len(states):
        current_state = states[idx]
        for sym in all_symbols:
            if sym == "EOF":
                continue
            next_state = lr0_goto(current_state, sym, grammar)
            if next_state and next_state not in state_indices:
                state_indices[next_state] = len(states)
                states.append(next_state)
        idx += 1

    return states


@dataclass
class SLR1Table:
    """Complete SLR(1) parsing table with ACTION and GOTO entries and conflict report."""

    grammar: Grammar
    states: list[frozenset[LR0Item]]
    action: dict[
        tuple[int, str], tuple[str, int]
    ]  # (state, terminal) -> ('S'/'R'/'ACC', target)
    goto: dict[tuple[int, str], int]  # (state, nonterminal) -> target_state
    conflicts: list[str]
    conflict_count: int


def build_slr1_table(grammar: Grammar) -> SLR1Table:
    """Construct SLR(1) ACTION and GOTO tables from grammar and report any conflicts."""
    states = build_lr0_automaton(grammar)
    state_map: dict[frozenset[LR0Item], int] = {
        state: i for i, state in enumerate(states)
    }

    first = compute_first(grammar)
    follow = compute_follow(grammar, first)

    action: dict[tuple[int, str], tuple[str, int]] = {}
    goto: dict[tuple[int, str], int] = {}
    conflicts: list[str] = []

    # Helper to insert an action with conflict checking
    def set_action(state_id: int, term: str, new_act: tuple[str, int]) -> None:
        key = (state_id, term)
        if key in action:
            existing = action[key]
            if existing != new_act:
                conflict_msg = (
                    f"Conflict in state {state_id} on terminal '{term}': "
                    f"existing={existing}, candidate={new_act}"
                )
                conflicts.append(conflict_msg)
        else:
            action[key] = new_act

    for i, state in enumerate(states):
        for item in state:
            next_sym = item.next_symbol(grammar)

            # Case 1: Dot before a terminal -> Shift
            if next_sym is not None and next_sym in grammar.terminals:
                target_state = lr0_goto(state, next_sym, grammar)
                if target_state in state_map:
                    target_id = state_map[target_state]
                    set_action(i, next_sym, ("S", target_id))

            # Case 2: Dot at the end
            elif next_sym is None:
                # Accept if augmented start production: Start -> Model •
                if item.prod_id == 0:
                    set_action(i, "EOF", ("ACC", 0))
                else:
                    prod = grammar.productions[item.prod_id]
                    # Reduce on every terminal in FOLLOW(head)
                    for a in follow[prod.head]:
                        set_action(i, a, ("R", item.prod_id))

        # Build GOTO table for nonterminals
        for nt in grammar.nonterminals:
            target_state = lr0_goto(state, nt, grammar)
            if target_state in state_map:
                goto[(i, nt)] = state_map[target_state]

    return SLR1Table(
        grammar=grammar,
        states=states,
        action=action,
        goto=goto,
        conflicts=conflicts,
        conflict_count=len(conflicts),
    )
