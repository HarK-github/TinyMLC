"""Tests for TMLC weight loader (Tests 13, 14, 15, 16, empty path, and path resolution)."""

from __future__ import annotations

import os
import pathlib

import pytest

from tmlc.errors import TmlcError
from tmlc.loader.weights import WeightLoader
from tmlc.parser.driver import ParserDriver
from tests.conftest import assert_cli_build_fails


def test_test13_missing_weight_file_e301() -> None:
    """Test 13: Missing .npy file produces E301."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/missing_w.tml")

    loader = WeightLoader()
    with pytest.raises(TmlcError) as exc_info:
        loader.load_weights(ast, base_dir="tests/fixtures")

    err = exc_info.value
    assert err.code == "E301", f"Expected E301, got {err.code}"
    assert err.line == 5
    assert_cli_build_fails("tests/fixtures/missing_w.tml", "E301")


def test_empty_path_string_e301() -> None:
    """Decision 5: Empty weight path string is treated as missing file (E301)."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/empty_path.tml")

    loader = WeightLoader()
    with pytest.raises(TmlcError) as exc_info:
        loader.load_weights(ast, base_dir="tests/fixtures")

    err = exc_info.value
    assert err.code == "E301", f"Expected E301, got {err.code}"
    assert err.line == 5
    assert_cli_build_fails("tests/fixtures/empty_path.tml", "E301")


def test_test14_bad_weight_shape_e302() -> None:
    """Test 14: Wrong weight matrix shape produces E302."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/bad_w_shape.tml")

    loader = WeightLoader()
    with pytest.raises(TmlcError) as exc_info:
        loader.load_weights(ast, base_dir="tests/fixtures")

    err = exc_info.value
    assert err.code == "E302", f"Expected E302, got {err.code}"
    assert err.line == 5
    assert_cli_build_fails("tests/fixtures/bad_w_shape.tml", "E302")


def test_test15_bad_bias_shape_e303() -> None:
    """Test 15: Wrong bias shape produces E303."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/bad_b_shape.tml")

    loader = WeightLoader()
    with pytest.raises(TmlcError) as exc_info:
        loader.load_weights(ast, base_dir="tests/fixtures")

    err = exc_info.value
    assert err.code == "E303", f"Expected E303, got {err.code}"
    assert err.line == 5
    assert_cli_build_fails("tests/fixtures/bad_b_shape.tml", "E303")


def test_test16_nan_weights_e304() -> None:
    """Test 16: Weights containing NaN produce E304."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/nan_w.tml")

    loader = WeightLoader()
    with pytest.raises(TmlcError) as exc_info:
        loader.load_weights(ast, base_dir="tests/fixtures")

    err = exc_info.value
    assert err.code == "E304", f"Expected E304, got {err.code}"
    assert err.line == 5
    assert_cli_build_fails("tests/fixtures/nan_w.tml", "E304")


def test_weights_resolve_relative_to_tml_file() -> None:
    """Weight paths resolve relative to .tml file location, not current working directory."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/bad_w_shape.tml")

    # Call from a different directory
    orig_cwd = os.getcwd()
    try:
        os.chdir("tests")
        loader = WeightLoader()
        # Even with cwd changed, resolving relative to 'fixtures' succeeds in locating file
        with pytest.raises(TmlcError) as exc_info:
            loader.load_weights(ast, base_dir="fixtures")
        # Raises E302 (shape mismatch), not E301 (missing file), confirming file was found
        assert exc_info.value.code == "E302"
    finally:
        os.chdir(orig_cwd)
