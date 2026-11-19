"""Grammar and Production representations for TMLC parser generator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Production:
    """A context-free grammar production rule: head -> body."""

    id: int
    head: str
    body: tuple[str, ...]

    def __str__(self) -> str:
        rhs = " ".join(self.body) if self.body else "ε"
        return f"{self.id}: {self.head} -> {rhs}"


@dataclass
class Grammar:
    """Context-free grammar with productions, terminals, and nonterminals."""

    start_symbol: str
    augmented_start: str
    terminals: set[str]
    nonterminals: set[str]
    productions: list[Production]

    def productions_for(self, nonterminal: str) -> list[Production]:
        """Return all productions whose head matches the given nonterminal."""
        return [p for p in self.productions if p.head == nonterminal]


def get_tmlc_grammar() -> Grammar:
    """Construct and return the formal augmented grammar for the TMLC language."""
    terminals: Final[set[str]] = {
        "MODEL",
        "IDENT",
        "LBRACE",
        "RBRACE",
        "INPUT",
        "OUTPUT",
        "COLON",
        "INT",
        "SEMICOLON",
        "DENSE",
        "LPAREN",
        "COMMA",
        "STRING",
        "RPAREN",
        "RELU",
        "SOFTMAX",
        "EOF",
    }

    nonterminals: Final[set[str]] = {
        "Start",
        "Model",
        "ModelBody",
        "InputDecl",
        "OutputDecl",
        "LayerList",
        "Layer",
        "DenseLayer",
        "ActivationLayer",
    }

    productions: list[Production] = [
        # Augmented production: 0
        Production(0, "Start", ("Model",)),
        # Model productions: 1
        Production(1, "Model", ("MODEL", "IDENT", "LBRACE", "ModelBody", "RBRACE")),
        # ModelBody: 2
        Production(2, "ModelBody", ("InputDecl", "OutputDecl", "LayerList")),
        # Declarations: 3, 4
        Production(3, "InputDecl", ("INPUT", "COLON", "INT", "SEMICOLON")),
        Production(4, "OutputDecl", ("OUTPUT", "COLON", "INT", "SEMICOLON")),
        # LayerList: 5, 6
        Production(5, "LayerList", ("LayerList", "Layer")),
        Production(6, "LayerList", ("Layer",)),
        # Layer: 7, 8
        Production(7, "Layer", ("DenseLayer",)),
        Production(8, "Layer", ("ActivationLayer",)),
        # DenseLayer: 9
        Production(
            9,
            "DenseLayer",
            (
                "DENSE",
                "LPAREN",
                "INT",
                "COMMA",
                "INT",
                "COMMA",
                "STRING",
                "COMMA",
                "STRING",
                "RPAREN",
                "SEMICOLON",
            ),
        ),
        # ActivationLayer: 10, 11
        Production(10, "ActivationLayer", ("RELU", "SEMICOLON")),
        Production(11, "ActivationLayer", ("SOFTMAX", "SEMICOLON")),
    ]

    return Grammar(
        start_symbol="Model",
        augmented_start="Start",
        terminals=terminals,
        nonterminals=nonterminals,
        productions=productions,
    )
