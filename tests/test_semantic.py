"""Tests for TMLC semantic analyzer (Tests 9, 11, 12, E204)."""

from __future__ import annotations

import pathlib

import pytest

from tmlc.errors import TmlcError
from tmlc.parser.driver import ParserDriver
from tmlc.semantic.analyzer import SemanticAnalyzer


def assert_no_model_c_written() -> None:
    """Verify that no generated/model.c file was created or modified."""
    model_c = pathlib.Path("generated/model.c")
    assert not model_c.exists(), "generated/model.c must not exist after invalid input"


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
    assert_no_model_c_written()


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
    assert_no_model_c_written()


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
    assert_no_model_c_written()


def test_no_dense_layer_e204() -> None:
    """Model with no Dense layer produces E204."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/no_dense.tml")

    analyzer = SemanticAnalyzer()
    with pytest.raises(TmlcError) as exc_info:
        analyzer.analyze(ast)

    err = exc_info.value
    assert err.code == "E204", f"Expected E204, got {err.code}"
    assert_no_model_c_written()


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
