"""Optimization pass: Dense + ReLU operator fusion."""

from __future__ import annotations

from tmlc.errors import TmlcError
from tmlc.ir.builder import IRProgram
from tmlc.ir.ops import IROp, OpKind


def fuse_dense_relu(program: IRProgram) -> IRProgram:
    """Fuse adjacent DENSE and RELU operations into single DENSE_RELU ops."""
    new_ops: list[IROp] = []
    i = 0
    ops = program.ops

    while i < len(ops):
        current_op = ops[i]

        # Check for DENSE immediately followed by RELU
        if (
            current_op.kind == OpKind.DENSE
            and i + 1 < len(ops)
            and ops[i + 1].kind == OpKind.RELU
        ):
            relu_op = ops[i + 1]
            if current_op.out_dim != relu_op.in_dim:
                raise TmlcError(
                    "E401",
                    f"IR inconsistency during fusion: DENSE out_dim {current_op.out_dim} "
                    f"does not match RELU in_dim {relu_op.in_dim}",
                )

            fused_op = IROp(
                kind=OpKind.DENSE_RELU,
                in_dim=current_op.in_dim,
                out_dim=current_op.out_dim,
                weights=current_op.weights,
                bias=current_op.bias,
                quantized_weights=current_op.quantized_weights,
                scale=current_op.scale,
            )
            new_ops.append(fused_op)
            i += 2
        else:
            new_ops.append(current_op)
            i += 1

    return IRProgram(
        name=program.name,
        input_dim=program.input_dim,
        output_dim=program.output_dim,
        ops=new_ops,
    )
