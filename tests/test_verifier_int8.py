"""Tests for numerical verification of int8 models against dequantized NumPy reference."""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import numpy as np
import pytest

from tmlc.errors import TmlcError
from tmlc.verifier.verify import ModelVerifier


def test_int8_tiny_matches_dequantized_numpy_reference() -> None:
    """Verify tiny model matches dequantized NumPy reference within atol=1e-5, rtol=1e-4."""
    verifier = ModelVerifier()
    test_vec = np.array([0.5, -0.2, 0.8, -0.4], dtype=np.float32)

    max_err, passed = verifier.verify_model(
        "examples/tiny.tml",
        input_vectors=[test_vec],
        out_dir="generated_int8/test_verify_tiny",
        quantize="int8",
    )
    assert passed
    assert max_err <= 1e-5, f"Max error {max_err} exceeds atol=1e-5"


def test_int8_mnist_matches_dequantized_numpy_reference() -> None:
    """Verify MNIST model int8 inference matches dequantized NumPy reference within atol=1e-5."""
    verifier = ModelVerifier()
    inputs_file = pathlib.Path("examples/test_inputs.npy")
    assert inputs_file.is_file()
    test_vectors = np.load(inputs_file)[:5]

    max_err, passed = verifier.verify_model(
        "examples/mnist.tml",
        input_vectors=test_vectors,
        out_dir="generated_int8/test_verify_mnist",
        quantize="int8",
    )
    assert passed
    assert max_err <= 1e-5, f"Max error {max_err} exceeds atol=1e-5"


def test_corrupted_scale_causes_verifier_failure() -> None:
    """Deliberately corrupting a scale factor in generated C causes verification failure (E601)."""
    verifier = ModelVerifier()
    out_dir = pathlib.Path("generated_int8/test_corrupt_scale")
    test_vec = np.array([0.5, -0.2, 0.8, -0.4], dtype=np.float32)

    # First run clean verification to generate files
    verifier.verify_model(
        "examples/tiny.tml",
        input_vectors=[test_vec],
        out_dir=out_dir,
        quantize="int8",
    )

    c_path = out_dir / "model.c"
    h_path = out_dir / "model.h"
    c_text = c_path.read_text(encoding="utf-8")

    # Corrupt layer1_scale by doubling it
    assert "layer1_scale =" in c_text
    corrupted_text = c_text.replace("layer1_scale =", "layer1_scale = 2.0f * ")
    c_path.write_text(corrupted_text, encoding="utf-8")

    c_out = verifier._compile_and_run_c(
        c_path=c_path,
        h_path=h_path,
        input_vector=test_vec,
        out_dim=2,
        out_dir=out_dir,
    )
    np_ref = verifier.numpy_reference_predict("examples/tiny.tml", test_vec, quantize="int8")

    # Outputs must differ and exceed tolerance
    diff = np.abs(c_out - np_ref)
    assert np.max(diff) > 1e-3
    assert not np.allclose(c_out, np_ref, atol=1e-5, rtol=1e-4)


def test_corrupted_int8_weight_causes_verifier_failure() -> None:
    """Deliberately corrupting an int8 weight in generated C causes verification failure (E601)."""
    verifier = ModelVerifier()
    out_dir = pathlib.Path("generated_int8/test_corrupt_weight")
    test_vec = np.array([0.5, -0.2, 0.8, -0.4], dtype=np.float32)

    # First run clean verification to generate files
    verifier.verify_model(
        "examples/tiny.tml",
        input_vectors=[test_vec],
        out_dir=out_dir,
        quantize="int8",
    )

    c_path = out_dir / "model.c"
    h_path = out_dir / "model.h"
    c_text = c_path.read_text(encoding="utf-8")

    # Corrupt layer1_weights: replace first array element with 127
    pattern = r"(static\s+const\s+int8_t\s+layer1_weights\[\d+\]\s*=\s*\{\s*\n\s*)(-?\d+)"
    corrupted_text = re.sub(pattern, r"\g<1>127", c_text, count=1)
    c_path.write_text(corrupted_text, encoding="utf-8")

    c_out = verifier._compile_and_run_c(
        c_path=c_path,
        h_path=h_path,
        input_vector=test_vec,
        out_dim=2,
        out_dir=out_dir,
    )
    np_ref = verifier.numpy_reference_predict("examples/tiny.tml", test_vec, quantize="int8")

    diff = np.abs(c_out - np_ref)
    assert np.max(diff) > 1e-4
    assert not np.allclose(c_out, np_ref, atol=1e-5, rtol=1e-4)


def test_cli_verify_int8() -> None:
    """CLI verify subcommand supports --quantize int8 and passes with exit code 0."""
    res = subprocess.run(
        [
            sys.executable,
            "main.py",
            "verify",
            "examples/tiny.tml",
            "--quantize",
            "int8",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"CLI int8 verify failed:\n{res.stderr}"
    assert "PASS" in res.stdout


def test_int8_reference_differs_from_unquantized_float32() -> None:
    """Ensure int8 verification reference is dequantized int8, not unquantized float32."""
    verifier = ModelVerifier()
    test_vec = np.array([0.5, -0.2, 0.8, -0.4], dtype=np.float32)

    f32_ref = verifier.numpy_reference_predict("examples/tiny.tml", test_vec, quantize=None)
    int8_ref = verifier.numpy_reference_predict("examples/tiny.tml", test_vec, quantize="int8")

    diff = np.abs(f32_ref - int8_ref)
    # Finite difference must exist due to quantization
    assert np.max(diff) > 0.0
