"""Quantization subsystem for TMLC."""

from __future__ import annotations

from tmlc.quantization.int8 import dequantize_weights, quantize_ir, quantize_weights

__all__ = ["quantize_weights", "dequantize_weights", "quantize_ir"]
