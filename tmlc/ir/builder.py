"""IR builder translating AST and weights into linear IR instructions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from tmlc.ast.nodes import ActivationNode, DenseNode, ModelNode
from tmlc.errors import TmlcError
from tmlc.ir.ops import IROp, OpKind
from tmlc.loader.weights import LoadedLayerWeights


@dataclass
class IRProgram:
    """Linear intermediate representation program for a model."""

    name: str
    input_dim: int
    output_dim: int
    ops: list[IROp]

    def format(self) -> str:
        """Format IR program as clean instruction listing."""
        lines = [
            f"; IR for model '{self.name}'",
            f"; input: {self.input_dim}, output: {self.output_dim}, {len(self.ops)} ops",
        ]
        for i, op in enumerate(self.ops, 1):
            lines.append(f"  {op.format(i)}")
        return "\n".join(lines)


def build_ir(
    model: ModelNode, loaded_weights: Sequence[LoadedLayerWeights]
) -> IRProgram:
    """Build linear IR from validated ModelNode and weights.

    Raises:
        TmlcError: E401 on internal shape inconsistency.
    """
    weight_map = {lw.layer: lw for lw in loaded_weights}
    ops: list[IROp] = []

    # 1. INPUT op
    ops.append(
        IROp(
            kind=OpKind.INPUT, in_dim=model.input_decl.dim, out_dim=model.input_decl.dim
        )
    )

    current_dim = model.input_decl.dim
    for layer in model.layers:
        if isinstance(layer, DenseNode):
            lw = weight_map.get(layer)
            if lw is None:
                raise TmlcError(
                    "E401",
                    f"Internal error: missing weights for layer {layer}",
                    layer.line,
                    layer.col,
                )
            if layer.in_features != current_dim:
                raise TmlcError(
                    "E401",
                    f"IR shape inconsistency: op expects {layer.in_features}, but current dim is {current_dim}",
                    layer.line,
                    layer.col,
                )
            ops.append(
                IROp(
                    kind=OpKind.DENSE,
                    in_dim=layer.in_features,
                    out_dim=layer.out_features,
                    weights=lw.weights,
                    bias=lw.bias,
                )
            )
            current_dim = layer.out_features

        elif isinstance(layer, ActivationNode):
            if layer.op == "ReLU":
                ops.append(
                    IROp(kind=OpKind.RELU, in_dim=current_dim, out_dim=current_dim)
                )
            elif layer.op == "Softmax":
                ops.append(
                    IROp(kind=OpKind.SOFTMAX, in_dim=current_dim, out_dim=current_dim)
                )
            else:
                raise TmlcError(
                    "E401", f"Unknown activation op: {layer.op}", layer.line, layer.col
                )

    # OUTPUT op
    if current_dim != model.output_decl.dim:
        raise TmlcError(
            "E401",
            f"IR output shape inconsistency: final dim is {current_dim}, declared is {model.output_decl.dim}",
            model.output_decl.line,
            model.output_decl.col,
        )

    ops.append(
        IROp(kind=OpKind.OUTPUT, in_dim=current_dim, out_dim=model.output_decl.dim)
    )

    return IRProgram(
        name=model.name,
        input_dim=model.input_decl.dim,
        output_dim=model.output_decl.dim,
        ops=ops,
    )
