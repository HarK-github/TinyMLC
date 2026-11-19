"""Tests for TMLC lexer (Tests 3, 4, negative dimension, and valid token streams)."""

from __future__ import annotations

import pathlib

import pytest

from tmlc.errors import TmlcError
from tmlc.lexer.lexer import Lexer


def assert_no_model_c_written() -> None:
    """Verify that no generated/model.c file was created or modified."""
    model_c = pathlib.Path("generated/model.c")
    assert not model_c.exists(), "generated/model.c must not exist after invalid input"


def test_test3_bad_char_e001() -> None:
    """Test 3: Unknown character '@' produces E001 with exact line and column."""
    fixture_path = pathlib.Path("tests/fixtures/bad_char.tml")
    assert fixture_path.exists()

    with pytest.raises(TmlcError) as exc_info:
        Lexer.from_file(fixture_path).tokenize()

    err = exc_info.value
    assert err.code == "E001", f"Expected E001, got {err.code}"
    assert err.line == 3, f"Expected line 3, got {err.line}"
    assert err.col == 5, f"Expected col 5, got {err.col}"
    assert "@" in err.message
    assert_no_model_c_written()


def test_test4_open_string_e002() -> None:
    """Test 4: Unterminated string produces E002 with line and column of the opening quote."""
    fixture_path = pathlib.Path("tests/fixtures/open_string.tml")
    assert fixture_path.exists()

    with pytest.raises(TmlcError) as exc_info:
        Lexer.from_file(fixture_path).tokenize()

    err = exc_info.value
    assert err.code == "E002", f"Expected E002, got {err.code}"
    assert err.line == 4, f"Expected line 4, got {err.line}"
    assert err.col == 17, f"Expected col 17, got {err.col}"
    assert_no_model_c_written()


def test_negative_value_rejected_as_e001() -> None:
    """Decision 3: Negative sign '-' in dimension is rejected by lexer as E001."""
    fixture_path = pathlib.Path("tests/fixtures/neg_dim.tml")
    assert fixture_path.exists()

    with pytest.raises(TmlcError) as exc_info:
        Lexer.from_file(fixture_path).tokenize()

    err = exc_info.value
    assert err.code == "E001", f"Expected E001, got {err.code}"
    assert err.line == 4, f"Expected line 4, got {err.line}"
    assert err.col == 11, f"Expected col 11, got {err.col}"
    assert "-" in err.message
    assert_no_model_c_written()


def test_tokenize_tiny_example() -> None:
    """Tokenize examples/tiny.tml and verify token sequence."""
    path = pathlib.Path("examples/tiny.tml")
    tokens = Lexer.from_file(path).tokenize()

    expected_types = [
        "MODEL",
        "IDENT",
        "LBRACE",
        "INPUT",
        "COLON",
        "INT",
        "SEMICOLON",
        "OUTPUT",
        "COLON",
        "INT",
        "SEMICOLON",
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
        "RELU",
        "SEMICOLON",
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
        "RBRACE",
        "EOF",
    ]
    actual_types = [t.type for t in tokens]
    assert actual_types == expected_types

    # Check first token location
    assert tokens[0].line == 2
    assert tokens[0].col == 1
    assert tokens[0].value == "model"


def test_tokenize_mnist_example() -> None:
    """Tokenize examples/mnist.tml and verify token count and structure."""
    path = pathlib.Path("examples/mnist.tml")
    tokens = Lexer.from_file(path).tokenize()

    assert tokens[-1].type == "EOF"
    model_tok = tokens[0]
    assert model_tok.type == "MODEL"
    assert model_tok.value == "model"
    assert model_tok.line == 2

    # Verify presence of Softmax token
    softmax_toks = [t for t in tokens if t.type == "SOFTMAX"]
    assert len(softmax_toks) == 1
    assert softmax_toks[0].value == "Softmax"


def test_comments_and_whitespace_line_tracking() -> None:
    """Ensure comments and whitespace update line and column counts correctly."""
    source = """// line 1 comment
# line 2 comment
/* line 3
   line 4 block comment */
model Foo {
}
"""
    tokens = Lexer(source).tokenize()
    assert tokens[0].type == "MODEL"
    assert tokens[0].line == 5
    assert tokens[0].col == 1

    assert tokens[1].type == "IDENT"
    assert tokens[1].value == "Foo"
    assert tokens[1].line == 5
    assert tokens[1].col == 7
