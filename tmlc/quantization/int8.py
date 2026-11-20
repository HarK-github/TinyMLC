"""Symmetric per-tensor int8 weight quantization for TMLC."""

from __future__ import annotations

import math

import numpy as np

from tmlc.errors import TmlcError
from tmlc.ir.builder import IRProgram
from tmlc.ir.ops import IROp, OpKind


def quantize_weights(weights: np.ndarray) -> tuple[np.ndarray, float]:
    """Perform symmetric per-tensor int8 weight quantization.

    Computes:
        scale = max(abs(W)) / 127.0
        q = clip(round(W / scale), -127, 127)

    For zero-weight matrices (max(abs(W)) == 0.0), scale is defined as 1.0f
    so that scale remains positive and finite, producing exact zero int8 weights.

    Args:
        weights: 2D floating-point weight matrix (in_dim, out_dim).

    Returns:
        tuple (q, scale) where q is np.ndarray with dtype np.int8 and
        scale is a positive, finite float.

    Raises:
        TmlcError: E304 if weights contain NaN or Inf.
    """
    if not np.all(np.isfinite(weights)):
        raise TmlcError("E304", "Cannot quantize weights containing NaN or Inf")

    max_val = float(np.max(np.abs(weights)))

    if max_val == 0.0:
        scale = 1.0
    else:
        scale = max_val / 127.0

    if not (scale > 0.0 and math.isfinite(scale)):
        raise TmlcError("E401", f"Calculated non-positive or non-finite int8 scale: {scale}")

    # Clip between -127 and 127 for strict symmetric int8 quantization
    q = np.clip(np.round(weights / scale), -127, 127).astype(np.int8)
    return q, float(scale)


def dequantize_weights(q: np.ndarray, scale: float) -> np.ndarray:
    """Dequantize int8 weights back to float32 reference representation.

    Computes:
        w_dequant = q.astype(np.float32) * scale

    Args:
        q: Quantized int8 weight matrix.
        scale: Positive, finite float scale factor.

    Returns:
        Dequantized np.ndarray with dtype np.float32.
    """
    return (q.astype(np.float32) * np.float32(scale)).astype(np.float32)


def quantize_ir(program: IRProgram) -> IRProgram:
    """Apply weight-only symmetric int8 quantization to an IR program.

    Replaces Dense and Fused Dense+ReLU weight representations with int8_t
    quantized weights and attaches per-tensor scale factors.
    Activations, bias vectors, and other operators remain unchanged float32.

    Args:
        program: The IRProgram (typically after operator fusion).

    Returns:
        New IRProgram containing quantized weights and scale metadata.

    Raises:
        TmlcError: E401 if a Dense operation is missing weights.
    """
    new_ops: list[IROp] = []

    for op in program.ops:
        if op.kind in (OpKind.DENSE, OpKind.DENSE_RELU):
            if op.weights is None:
                raise TmlcError(
                    "E401",
                    f"Dense operation {op.kind.value} missing weights during quantization pass",
                )
            q, scale = quantize_weights(op.weights)
            quantized_op = IROp(
                kind=op.kind,
                in_dim=op.in_dim,
                out_dim=op.out_dim,
                weights=op.weights,
                bias=op.bias,
                input_buf=op.input_buf,
                output_buf=op.output_buf,
                quantized_weights=q,
                scale=scale,
            )
            new_ops.append(quantized_op)
        else:
            new_ops.append(op)

    return IRProgram(
        name=program.name,
        input_dim=program.input_dim,
        output_dim=program.output_dim,
        ops=new_ops,
    )
