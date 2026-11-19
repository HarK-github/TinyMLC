"""Computation of FIRST and FOLLOW sets for context-free grammars."""

from __future__ import annotations

from collections.abc import Sequence

from tmlc.parser.grammar import Grammar


def compute_first(grammar: Grammar) -> dict[str, set[str]]:
    """Compute the FIRST set for each terminal and nonterminal in the grammar."""
    first: dict[str, set[str]] = {}

    # For every terminal, FIRST is the terminal itself
    for t in grammar.terminals:
        first[t] = {t}

    # For every nonterminal, initialize as empty set
    for nt in grammar.nonterminals:
        first[nt] = set()

    # Fixed-point iteration
    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            head = prod.head
            body = prod.body

            if not body:
                if "ε" not in first[head]:
                    first[head].add("ε")
                    changed = True
                continue

            # Scan symbols in body
            all_nullable = True
            for sym in body:
                sym_first = first.get(sym, set())
                add_set = sym_first - {"ε"}
                if not add_set.issubset(first[head]):
                    first[head].update(add_set)
                    changed = True

                if "ε" not in sym_first:
                    all_nullable = False
                    break

            if all_nullable and "ε" not in first[head]:
                first[head].add("ε")
                changed = True

    return first


def compute_first_of_sequence(
    symbols: Sequence[str],
    first: dict[str, set[str]],
) -> set[str]:
    """Compute FIRST set for a sequence of grammar symbols."""
    result: set[str] = set()
    all_nullable = True

    for sym in symbols:
        sym_first = first.get(sym, {sym})
        result.update(sym_first - {"ε"})
        if "ε" not in sym_first:
            all_nullable = False
            break

    if all_nullable:
        result.add("ε")

    return result


def compute_follow(
    grammar: Grammar,
    first: dict[str, set[str]],
) -> dict[str, set[str]]:
    """Compute FOLLOW set for each nonterminal in the grammar."""
    follow: dict[str, set[str]] = {nt: set() for nt in grammar.nonterminals}

    # The augmented start symbol gets EOF in its FOLLOW set
    follow[grammar.augmented_start].add("EOF")
    follow[grammar.start_symbol].add("EOF")

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            head = prod.head
            body = prod.body

            for i, sym in enumerate(body):
                if sym in grammar.nonterminals:
                    # Look at remaining symbols β after sym
                    beta = body[i + 1 :]
                    beta_first = compute_first_of_sequence(beta, first)

                    add_first = beta_first - {"ε"}
                    if not add_first.issubset(follow[sym]):
                        follow[sym].update(add_first)
                        changed = True

                    if ("ε" in beta_first or not beta) and not follow[head].issubset(
                        follow[sym]
                    ):
                        follow[sym].update(follow[head])
                        changed = True

    return follow
