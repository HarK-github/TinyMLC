"""Intermediate Representation (IR) op definitions for TMLC."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


class OpKind(Enum):
    """Enumeration of IR operation types."""

    INPUT = "INPUT"
    DENSE = "DENSE"
    RELU = "RELU"
    SOFTMAX = "SOFTMAX"
    DENSE_RELU = "DENSE_RELU"
    OUTPUT = "OUTPUT"


@dataclass(frozen=True)
class IROp:
    """An operation in the TMLC Intermediate Representation.

    Attributes:
        kind: The operation kind (e.g. DENSE, RELU, DENSE_RELU).
        in_dim: Input vector dimension.
        out_dim: Output vector dimension.
        weights: Optional weight matrix (in_dim, out_dim) for Dense ops.
        bias: Optional bias vector (out_dim,) for Dense ops.
        input_buf: Assigned input buffer name (e.g. 'input', 'buf_a', 'buf_b').
        output_buf: Assigned output buffer name (e.g. 'buf_a', 'buf_b', 'output').
    """

    kind: OpKind
    in_dim: int
    out_dim: int
    weights: np.ndarray | None = None
    bias: np.ndarray | None = None
    input_buf: str = ""
    output_buf: str = ""

    def format(self, op_index: int) -> str:
        """Format op as an SSA-like instruction string."""
        buf_info = (
            f" [{self.input_buf} -> {self.output_buf}]"
            if self.input_buf and self.output_buf
            else ""
        )
        if self.kind == OpKind.INPUT:
            return f"%{op_index} = INPUT(dim={self.out_dim}){buf_info}"
        if self.kind == OpKind.OUTPUT:
            return f"%{op_index} = OUTPUT(dim={self.in_dim}){buf_info}"
        if self.kind == OpKind.DENSE:
            return f"%{op_index} = DENSE({self.in_dim} -> {self.out_dim}){buf_info}"
        if self.kind == OpKind.RELU:
            return f"%{op_index} = RELU(dim={self.in_dim}){buf_info}"
        if self.kind == OpKind.SOFTMAX:
            return f"%{op_index} = SOFTMAX(dim={self.in_dim}){buf_info}"
        if self.kind == OpKind.DENSE_RELU:
            return (
                f"%{op_index} = DENSE_RELU({self.in_dim} -> {self.out_dim}){buf_info}"
            )
        return f"%{op_index} = {self.kind.value}({self.in_dim} -> {self.out_dim}){buf_info}"
