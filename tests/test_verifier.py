"""Tests for TMLC model verification and independent NumPy baseline (Tests 2, 18, E601, E602)."""

from __future__ import annotations

import pathlib

import numpy as np
import pytest

from tmlc.errors import TmlcError
from tmlc.verifier.verify import ModelVerifier


def test_test2_verify_tiny_course_example() -> None:
    """Test 2: Course example Dense(4,8)->ReLU->Dense(8,2) passes numerical verification."""
    verifier = ModelVerifier()
    # Test on arbitrary input vector
    test_vec = np.array([0.5, -0.2, 0.8, -0.4], dtype=np.float32)
    max_err, passed = verifier.verify_model(
        "examples/tiny.tml",
        input_vectors=[test_vec],
    )
    assert passed, f"Verification failed with max error: {max_err}"
    assert max_err <= 1e-5, f"Error {max_err} exceeds atol=1e-5"


def test_test18_verify_mnist_five_vectors() -> None:
    """Test 18: Five distinct MNIST test vectors pass independent NumPy verification."""
    verifier = ModelVerifier()
    inputs_file = pathlib.Path("examples/test_inputs.npy")
    assert inputs_file.is_file(), "Test inputs file examples/test_inputs.npy missing"
    test_vectors = np.load(inputs_file)
    assert len(test_vectors) >= 5

    max_err, passed = verifier.verify_model(
        "examples/mnist.tml",
        input_vectors=test_vectors[:5],
    )
    assert passed, f"Verification failed with max error: {max_err}"
    assert max_err <= 1e-5, f"Error {max_err} exceeds atol=1e-5"


def test_verifier_independent_numpy_reference() -> None:
    """Independent NumPy reference executes forward pass matching loop dot-product semantics."""
    verifier = ModelVerifier()
    test_vec = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    ref_out = verifier.numpy_reference_predict("examples/tiny.tml", test_vec)
    assert ref_out.shape == (2,)
    assert ref_out.dtype == np.float32


def test_verifier_reports_e602_on_gcc_compile_error() -> None:
    """Verifier raises E602 if compilation fails."""
    verifier = ModelVerifier()
    # Provide non-existent or invalid C file
    with pytest.raises(TmlcError) as exc_info:
        verifier._compile_and_run_c(
            c_path=pathlib.Path("non_existent_file.c"),
            h_path=pathlib.Path("non_existent_file.h"),
            input_vector=np.zeros(4, dtype=np.float32),
            out_dim=2,
            out_dir=pathlib.Path("generated/tmp_test"),
        )
    err = exc_info.value
    assert err.code == "E602"
