"""Tests for TMLC parser generator and AST construction (Tests 5, 6, 7, 8, 10, AST, tables)."""

from __future__ import annotations

import pathlib

import pytest

from tmlc.ast.nodes import ActivationNode, DenseNode, ModelNode
from tmlc.errors import TmlcError
from tmlc.parser.driver import ParserDriver
from tmlc.parser.grammar import get_tmlc_grammar
from tmlc.parser.lr0 import build_slr1_table
from tests.conftest import assert_cli_build_fails


def assert_no_model_c_written() -> None:
    """Verify that no generated/model.c file was created or modified."""
    model_c = pathlib.Path("generated/model.c")
    assert not model_c.exists(), "generated/model.c must not exist after invalid input"


def test_test5_missing_semicolon_e101() -> None:
    """Test 5: Missing semicolon produces E101."""
    fixture_path = pathlib.Path("tests/fixtures/no_semi.tml")
    assert fixture_path.exists()

    driver = ParserDriver()
    with pytest.raises(TmlcError) as exc_info:
        driver.parse_file(fixture_path)

    err = exc_info.value
    assert err.code == "E101", f"Expected E101, got {err.code}"
    assert err.line == 4, f"Expected line 4, got {err.line}"
    assert_cli_build_fails(fixture_path, "E101")


def test_test6_trailing_tokens_e101() -> None:
    """Test 6: Extra tokens after closing brace produce E101."""
    fixture_path = pathlib.Path("tests/fixtures/trailing.tml")
    assert fixture_path.exists()

    driver = ParserDriver()
    with pytest.raises(TmlcError) as exc_info:
        driver.parse_file(fixture_path)

    err = exc_info.value
    assert err.code == "E101", f"Expected E101, got {err.code}"
    assert err.line == 7, f"Expected line 7, got {err.line}"
    assert_cli_build_fails(fixture_path, "E101")


def test_test7_missing_input_decl_e101() -> None:
    """Test 7: Missing input declaration produces E101."""
    fixture_path = pathlib.Path("tests/fixtures/no_input.tml")
    assert fixture_path.exists()

    driver = ParserDriver()
    with pytest.raises(TmlcError) as exc_info:
        driver.parse_file(fixture_path)

    err = exc_info.value
    assert err.code == "E101", f"Expected E101, got {err.code}"
    assert err.line == 3, f"Expected line 3, got {err.line}"
    assert_cli_build_fails(fixture_path, "E101")


def test_test8_missing_output_decl_e101() -> None:
    """Test 8: Missing output declaration produces E101."""
    fixture_path = pathlib.Path("tests/fixtures/no_output.tml")
    assert fixture_path.exists()

    driver = ParserDriver()
    with pytest.raises(TmlcError) as exc_info:
        driver.parse_file(fixture_path)

    err = exc_info.value
    assert err.code == "E101", f"Expected E101, got {err.code}"
    assert err.line == 4, f"Expected line 4, got {err.line}"
    assert_cli_build_fails(fixture_path, "E101")


def test_test10_unknown_layer_e101() -> None:
    """Test 10: Unknown layer name (Conv2D) produces E101."""
    fixture_path = pathlib.Path("tests/fixtures/unknown_layer.tml")
    assert fixture_path.exists()

    driver = ParserDriver()
    with pytest.raises(TmlcError) as exc_info:
        driver.parse_file(fixture_path)

    err = exc_info.value
    assert err.code == "E101", f"Expected E101, got {err.code}"
    assert err.line == 5, f"Expected line 5, got {err.line}"
    assert_cli_build_fails(fixture_path, "E101")


def test_slr1_table_is_conflict_free() -> None:
    """Verify that SLR(1) table construction has 0 shift/reduce or reduce/reduce conflicts."""
    grammar = get_tmlc_grammar()
    table = build_slr1_table(grammar)
    assert table.conflict_count == 0, (
        f"Grammar has {table.conflict_count} SLR(1) conflicts!"
    )


def test_parse_tiny_ast_construction() -> None:
    """Parse examples/tiny.tml and verify constructed AST."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/tiny.tml")

    assert isinstance(ast, ModelNode)
    assert ast.name == "Tiny"
    assert ast.input_decl.dim == 4
    assert ast.output_decl.dim == 2
    assert len(ast.layers) == 3

    assert isinstance(ast.layers[0], DenseNode)
    assert ast.layers[0].in_features == 4
    assert ast.layers[0].out_features == 8
    assert ast.layers[0].weight_path == "weights/tiny_w1.npy"

    assert isinstance(ast.layers[1], ActivationNode)
    assert ast.layers[1].op == "ReLU"

    assert isinstance(ast.layers[2], DenseNode)
    assert ast.layers[2].in_features == 8
    assert ast.layers[2].out_features == 2


def test_parse_mnist_ast_construction() -> None:
    """Parse examples/mnist.tml and verify constructed AST."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/mnist.tml")

    assert isinstance(ast, ModelNode)
    assert ast.name == "MNIST"
    assert ast.input_decl.dim == 784
    assert ast.output_decl.dim == 10
    assert len(ast.layers) == 6

    # Dense(784, 128) -> ReLU -> Dense(128, 64) -> ReLU -> Dense(64, 10) -> Softmax
    layer_types = [type(layer).__name__ for layer in ast.layers]
    assert layer_types == [
        "DenseNode",
        "ActivationNode",
        "DenseNode",
        "ActivationNode",
        "DenseNode",
        "ActivationNode",
    ]


def test_parse_trace_recording() -> None:
    """Verify that --trace records shift and reduce actions."""
    driver = ParserDriver()
    trace_log: list[str] = []
    ast = driver.parse_file("examples/tiny.tml", trace_callback=trace_log.append)
    assert isinstance(ast, ModelNode)

    shifts = [line for line in trace_log if line.startswith("SHIFT")]
    reduces = [line for line in trace_log if line.startswith("REDUCE")]
    assert len(shifts) > 0
    assert len(reduces) > 0
