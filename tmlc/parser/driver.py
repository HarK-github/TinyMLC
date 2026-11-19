"""Shift-reduce LR driver for TMLC parser."""

from __future__ import annotations

import pathlib
from collections.abc import Callable
from typing import Any

from tmlc.ast.builder import reduce_action
from tmlc.ast.nodes import ModelNode
from tmlc.errors import TmlcError
from tmlc.lexer.lexer import Lexer, Token
from tmlc.parser.grammar import get_tmlc_grammar
from tmlc.parser.lr0 import SLR1Table, build_slr1_table


class ParserDriver:
    """Shift-reduce LR parsing engine driven by an SLR(1) table."""

    def __init__(self, table: SLR1Table | None = None) -> None:
        if table is None:
            grammar = get_tmlc_grammar()
            self.table: SLR1Table = build_slr1_table(grammar)
        else:
            self.table = table

    def parse_tokens(
        self,
        tokens: list[Token],
        trace_callback: Callable[[str], None] | None = None,
    ) -> ModelNode:
        """Parse a list of tokens into an AST ModelNode.

        Args:
            tokens: Sequence of lexical tokens terminated by EOF.
            trace_callback: Optional callback receiving trace log strings.

        Returns:
            The root ModelNode of the parsed AST.

        Raises:
            TmlcError: E101 on syntax error / unexpected token.
        """
        state_stack: list[int] = [0]
        val_stack: list[Any] = []
        token_idx: int = 0

        while token_idx < len(tokens):
            current_state = state_stack[-1]
            tok = tokens[token_idx]

            action_key = (current_state, tok.type)
            if action_key not in self.table.action:
                expected_terms = [
                    t for (s, t) in self.table.action if s == current_state
                ]
                expected_str = ", ".join(sorted(expected_terms))
                val_repr = repr(tok.value) if tok.type != "EOF" else "end of input"
                msg = (
                    f"Unexpected token {val_repr} (type: '{tok.type}'). "
                    f"Expected one of: [{expected_str}]"
                )
                raise TmlcError("E101", msg, tok.line, tok.col)

            act_type, target = self.table.action[action_key]

            if act_type == "S":
                # Shift
                if trace_callback:
                    trace_callback(
                        f"SHIFT   token '{tok.type}'({tok.value!r}) -> push State {target}"
                    )
                state_stack.append(target)
                val_stack.append(tok)
                token_idx += 1

            elif act_type == "R":
                # Reduce
                prod = self.table.grammar.productions[target]
                body_len = len(prod.body)

                rhs: list[Any] = []
                if body_len > 0:
                    del state_stack[-body_len:]
                    for _ in range(body_len):
                        rhs.append(val_stack.pop())
                    rhs.reverse()

                reduced_node = reduce_action(prod.id, rhs)

                top_state = state_stack[-1]
                goto_key = (top_state, prod.head)
                if goto_key not in self.table.goto:
                    raise TmlcError(
                        "E101",
                        f"No GOTO entry from state {top_state} on nonterminal '{prod.head}'",
                        tok.line,
                        tok.col,
                    )

                next_state = self.table.goto[goto_key]
                if trace_callback:
                    trace_callback(
                        f"REDUCE  rule {prod.id}: {prod.head} -> {' '.join(prod.body)} "
                        f"-> Goto State {next_state}"
                    )
                state_stack.append(next_state)
                val_stack.append(reduced_node)

            elif act_type == "ACC":
                # Accept
                if trace_callback:
                    trace_callback("ACCEPT  Parsing successfully completed")
                res = val_stack[0]
                if not isinstance(res, ModelNode):
                    raise TmlcError(
                        "E101",
                        f"Expected ModelNode at root of parse tree, got {type(res).__name__}",
                        tok.line,
                        tok.col,
                    )
                return res

            else:
                raise ValueError(f"Unknown action type: {act_type}")

        raise TmlcError(
            "E101", "Unexpected end of input before model was closed", None, None
        )

    def parse_source(
        self,
        source: str,
        trace_callback: Callable[[str], None] | None = None,
    ) -> ModelNode:
        """Lex and parse source string into an AST ModelNode."""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        return self.parse_tokens(tokens, trace_callback=trace_callback)

    def parse_file(
        self,
        path: str | pathlib.Path,
        trace_callback: Callable[[str], None] | None = None,
    ) -> ModelNode:
        """Lex and parse source file into an AST ModelNode."""
        lexer = Lexer.from_file(path)
        tokens = lexer.tokenize()
        return self.parse_tokens(tokens, trace_callback=trace_callback)
