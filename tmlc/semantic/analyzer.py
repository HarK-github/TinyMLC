"""Semantic analyzer checking layer dimensions, declarations, and topology."""

from __future__ import annotations

from tmlc.ast.nodes import DenseNode, ModelNode
from tmlc.errors import TmlcError


class SemanticAnalyzer:
    """Validates model dimensions, topology, and consistency against specification."""

    def analyze(self, model: ModelNode) -> None:
        """Perform full semantic validation on the parsed ModelNode.

        Raises:
            TmlcError: E201 (dimension mismatch), E202 (non-positive dimension),
                       E203 (output dimension mismatch), or E204 (no Dense layer).
        """
        # E202: Check declared dimensions are positive
        if model.input_decl.dim <= 0:
            raise TmlcError(
                "E202",
                f"Model input dimension must be positive, got {model.input_decl.dim}",
                model.input_decl.line,
                model.input_decl.col,
            )

        if model.output_decl.dim <= 0:
            raise TmlcError(
                "E202",
                f"Model output dimension must be positive, got {model.output_decl.dim}",
                model.output_decl.line,
                model.output_decl.col,
            )

        # E204: Check that model has at least one Dense layer
        dense_layers: list[DenseNode] = [
            layer for layer in model.layers if isinstance(layer, DenseNode)
        ]
        if not dense_layers:
            raise TmlcError(
                "E204",
                "Model contains no Dense layer; TinyML models must specify at least one linear transform",
                model.line,
                model.col,
            )

        # E202: Check each Dense layer has positive dimensions
        for layer in dense_layers:
            if layer.in_features <= 0 or layer.out_features <= 0:
                raise TmlcError(
                    "E202",
                    f"Dense layer dimensions must be positive, got ({layer.in_features}, {layer.out_features})",
                    layer.line,
                    layer.col,
                )

        # E201: Check layer dimension chaining from input to layers
        current_dim = model.input_decl.dim
        for node in model.layers:
            if isinstance(node, DenseNode):
                if node.in_features != current_dim:
                    raise TmlcError(
                        "E201",
                        f"Layer input dimension mismatch: layer expects {node.in_features}, "
                        f"but previous output/input dimension is {current_dim}",
                        node.line,
                        node.col,
                    )
                current_dim = node.out_features

        # E203: Check last Dense layer matches model output declaration
        last_dense = dense_layers[-1]
        if last_dense.out_features != model.output_decl.dim:
            raise TmlcError(
                "E203",
                f"Last Dense layer output dimension ({last_dense.out_features}) does not match "
                f"model declared output dimension ({model.output_decl.dim})",
                last_dense.line,
                last_dense.col,
            )
