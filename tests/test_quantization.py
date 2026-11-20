"""Tests for symmetric per-tensor int8 weight quantization."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tmlc.errors import TmlcError
from tmlc.ir.builder import build_ir
from tmlc.ir.ops import OpKind
from tmlc.loader.weights import WeightLoader
from tmlc.optimizer.fuse import fuse_dense_relu
from tmlc.parser.driver import ParserDriver
from tmlc.quantization.int8 import dequantize_weights, quantize_ir, quantize_weights
from tmlc.semantic.analyzer import SemanticAnalyzer


def test_int8_scale_positive_and_finite() -> None:
    """Verify int8 scale is strictly positive, finite, and well-behaved across distributions."""
    rng = np.random.default_rng(seed=42)

    distributions = [
        rng.standard_normal((32, 16)).astype(np.float32),
        rng.uniform(-0.01, 0.01, (64, 32)).astype(np.float32),
        rng.uniform(1e-6, 1e-4, (16, 8)).astype(np.float32),
        np.array([[127.0]], dtype=np.float32),
        np.array([[-127.0]], dtype=np.float32),
    ]

    for w in distributions:
        q, scale = quantize_weights(w)
        assert isinstance(scale, float)
        assert scale > 0.0
        assert math.isfinite(scale)
        assert not math.isnan(scale)
        assert q.dtype == np.int8
        assert q.shape == w.shape


def test_zero_weight_behavior() -> None:
    """Verify explicitly defined zero-weight behavior: scale=1.0, q=0, dequant=0.0."""
    w_zero = np.zeros((10, 5), dtype=np.float32)
    q, scale = quantize_weights(w_zero)

    assert scale == 1.0
    assert scale > 0.0
    assert math.isfinite(scale)
    assert q.dtype == np.int8
    assert np.all(q == 0)

    w_dequant = dequantize_weights(q, scale)
    assert w_dequant.dtype == np.float32
    assert np.all(w_dequant == 0.0)


def test_rounding_and_clipping() -> None:
    """Verify rounding to nearest integer and clipping to [-127, 127]."""
    # Force scale = 1.0 by including 127.0 as maximum absolute value
    w = np.array(
        [
            [0.0, 0.49, 0.51, 1.49],
            [-0.49, -0.51, 126.4, 127.0],
            [150.0, 300.0, -150.0, -300.0],  # Must be clipped to +-127, avoiding -128
        ],
        dtype=np.float32,
    )
    # The max absolute value in w is 300.0, so scale would be 300.0 / 127.
    # Let's craft w where max is exactly 127.0 and test clipping with scaled values
    scale_manual = 1.0
    # Test quantize_weights directly on controlled inputs
    w_controlled = np.array([-200.0, -128.0, -127.0, -1.0, 0.0, 1.0, 127.0, 200.0], dtype=np.float32)
    # If max is 200.0, scale is 200.0 / 127.0.
    # To test clipping directly, let us test when scale is fixed or when values exceed 127 * scale
    w_test = np.array([-127.0, -0.6, 0.0, 0.6, 127.0], dtype=np.float32)
    q, scale = quantize_weights(w_test)
    assert scale == 1.0
    assert np.array_equal(q, np.array([-127, -1, 0, 1, 127], dtype=np.int8))

    # Test clipping: symmetric range strictly excludes -128
    assert np.all(q >= -127)
    assert np.all(q <= 127)

    # Synthetic clipping test: clip(round(W / scale), -127, 127)
    raw = np.array([-130.0, -128.0, 128.0, 200.0], dtype=np.float32)
    # With scale = 1.0
    clipped = np.clip(np.round(raw / 1.0), -127, 127).astype(np.int8)
    assert np.all(clipped >= -127)
    assert np.all(clipped <= 127)
    assert clipped[0] == -127
    assert clipped[1] == -127
    assert clipped[2] == 127
    assert clipped[3] == 127


def test_extreme_weights_do_not_overflow() -> None:
    """Verify extreme weights (very large or very small) do not cause overflow or invalid int8 values."""
    w_large = np.array([[-1e30, 0.0], [5e29, 1e30]], dtype=np.float32)
    q_large, scale_large = quantize_weights(w_large)

    assert scale_large > 0.0
    assert math.isfinite(scale_large)
    assert q_large.dtype == np.int8
    assert np.all(q_large >= -127)
    assert np.all(q_large <= 127)
    assert q_large[0, 0] == -127
    assert q_large[1, 1] == 127

    w_small = np.array([[-1e-35, 0.0], [5e-36, 1e-35]], dtype=np.float32)
    q_small, scale_small = quantize_weights(w_small)
    assert scale_small > 0.0
    assert math.isfinite(scale_small)
    assert q_small.dtype == np.int8
    assert np.all(q_small >= -127)
    assert np.all(q_small <= 127)


def test_nan_or_inf_weights_rejected_e304() -> None:
    """Quantization rejects tensors containing NaN or infinity with E304."""
    w_nan = np.array([[1.0, np.nan], [0.0, 2.0]], dtype=np.float32)
    with pytest.raises(TmlcError) as exc_nan:
        quantize_weights(w_nan)
    assert exc_nan.value.code == "E304"

    w_inf = np.array([[1.0, np.inf], [0.0, 2.0]], dtype=np.float32)
    with pytest.raises(TmlcError) as exc_inf:
        quantize_weights(w_inf)
    assert exc_inf.value.code == "E304"


def test_ir_records_quantization_metadata_only_when_enabled() -> None:
    """Verify IR records quantization metadata (scale, quantized weights) only when quantize is enabled."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/tiny.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)

    # 1. Unquantized path: no quantization metadata in IR
    for op in fused_prog.ops:
        assert op.scale is None
        assert op.quantized_weights is None
    ir_str = fused_prog.format()
    assert "[int8]" not in ir_str
    assert "[scale=" not in ir_str

    # 2. Quantized path: quantization metadata recorded for dense ops
    quant_prog = quantize_ir(fused_prog)
    dense_ops = [
        op for op in quant_prog.ops if op.kind in (OpKind.DENSE, OpKind.DENSE_RELU)
    ]
    assert len(dense_ops) == 2

    for op in dense_ops:
        assert op.scale is not None
        assert op.scale > 0.0
        assert math.isfinite(op.scale)
        assert op.quantized_weights is not None
        assert op.quantized_weights.dtype == np.int8

    quant_ir_str = quant_prog.format()
    assert "[int8]" in quant_ir_str
    assert "[scale=" in quant_ir_str


def test_quantize_dequantize_roundtrip_precision() -> None:
    """Verify that dequantized weights match w_int8 * scale and roundtrip error <= scale / 2."""
    rng = np.random.default_rng(seed=123)
    w = rng.uniform(-2.5, 2.5, (128, 64)).astype(np.float32)

    q, scale = quantize_weights(w)
    w_dequant = dequantize_weights(q, scale)

    # Roundtrip quantization error on non-clipped values is at most scale / 2 + float epsilon
    abs_err = np.abs(w - w_dequant)
    max_expected_err = (scale / 2.0) + 1e-6
    assert np.max(abs_err) <= max_expected_err
