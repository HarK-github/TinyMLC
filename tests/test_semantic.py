"""Tests for TMLC semantic analyzer (Tests 9, 11, 12, E204)."""

from __future__ import annotations

import pathlib

import pytest

from tmlc.errors import TmlcError
from tmlc.parser.driver import ParserDriver
from tmlc.semantic.analyzer import SemanticAnalyzer
from tests.conftest import assert_cli_build_fails


def test_test9_zero_dimension_e202() -> None:
    """Test 9: Zero dimension produces E202."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/zero_dim.tml")

    analyzer = SemanticAnalyzer()
    with pytest.raises(TmlcError) as exc_info:
        analyzer.analyze(ast)

    err = exc_info.value
    assert err.code == "E202", f"Expected E202, got {err.code}"
    assert err.line == 5
    assert_cli_build_fails("tests/fixtures/zero_dim.tml", "E202")


def test_test11_dimension_mismatch_e201() -> None:
    """Test 11: Dense(784, 128) then Dense(64, 10) produces E201."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/mismatch.tml")

    analyzer = SemanticAnalyzer()
    with pytest.raises(TmlcError) as exc_info:
        analyzer.analyze(ast)

    err = exc_info.value
    assert err.code == "E201", f"Expected E201, got {err.code}"
    assert err.line == 7
    assert_cli_build_fails("tests/fixtures/mismatch.tml", "E201")


def test_test12_output_mismatch_e203() -> None:
    """Test 12: Last Dense output does not match output declaration produces E203."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/bad_output.tml")

    analyzer = SemanticAnalyzer()
    with pytest.raises(TmlcError) as exc_info:
        analyzer.analyze(ast)

    err = exc_info.value
    assert err.code == "E203", f"Expected E203, got {err.code}"
    assert err.line == 7
    assert_cli_build_fails("tests/fixtures/bad_output.tml", "E203")


def test_no_dense_layer_e204() -> None:
    """Model with no Dense layer produces E204."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/no_dense.tml")

    analyzer = SemanticAnalyzer()
    with pytest.raises(TmlcError) as exc_info:
        analyzer.analyze(ast)

    err = exc_info.value
    assert err.code == "E204", f"Expected E204, got {err.code}"
    assert_cli_build_fails("tests/fixtures/no_dense.tml", "E204")


def test_valid_tiny_semantic_pass() -> None:
    """Semantic analysis on tiny.tml passes without error."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/tiny.tml")
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)


def test_valid_mnist_semantic_pass() -> None:
    """Semantic analysis on mnist.tml passes without error."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/mnist.tml")
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
