"""Formatting and inspection tools for parser tables and conflict reports."""

from __future__ import annotations

from tmlc.parser.lr0 import SLR1Table


def format_slr1_table(table: SLR1Table) -> str:
    """Format SLR(1) parsing table with state items, ACTION, GOTO, and conflict report."""
    lines: list[str] = [
        "============================================================",
        "              TMLC SLR(1) PARSING TABLE SUMMARY             ",
        "============================================================",
        f"Grammar Nonterminals : {len(table.grammar.nonterminals)}",
        f"Grammar Terminals    : {len(table.grammar.terminals)}",
        f"Grammar Productions  : {len(table.grammar.productions)}",
        f"LR(0) Total States   : {len(table.states)}",
        f"SLR(1) Conflicts     : {table.conflict_count}",
        "------------------------------------------------------------",
    ]

    if table.conflict_count > 0:
        lines.append("CONFLICT DETAILS:")
        for c in table.conflicts:
            lines.append(f"  * {c}")
        lines.append("------------------------------------------------------------")
    else:
        lines.append("Table is conflict-free: YES (0 conflicts)")
        lines.append("------------------------------------------------------------")

    # Detailed state list
    for i, state in enumerate(table.states):
        lines.append(f"\nState {i}:")
        for item in sorted(state, key=lambda it: (it.prod_id, it.dot)):
            lines.append(f"    {item.format(table.grammar)}")

        # Actions from state i
        state_actions = [
            (term, act) for (s, term), act in table.action.items() if s == i
        ]
        if state_actions:
            lines.append("  ACTION:")
            for term, act in sorted(state_actions, key=lambda x: x[0]):
                act_str = (
                    f"Shift {act[1]}"
                    if act[0] == "S"
                    else (
                        f"Reduce ({act[1]}: {table.grammar.productions[act[1]]})"
                        if act[0] == "R"
                        else "ACCEPT"
                    )
                )
                lines.append(f"    on '{term}' -> {act_str}")

        # Gotos from state i
        state_gotos = [(nt, tgt) for (s, nt), tgt in table.goto.items() if s == i]
        if state_gotos:
            lines.append("  GOTO:")
            for nt, tgt in sorted(state_gotos, key=lambda x: x[0]):
                lines.append(f"    on '{nt}' -> State {tgt}")

    return "\n".join(lines)
