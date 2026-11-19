"""Abstract Syntax Tree (AST) node definitions for TMLC."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes."""

    line: int
    col: int


@dataclass(frozen=True)
class InputDeclNode(ASTNode):
    """Input dimension declaration (e.g. 'input: 784;')."""

    dim: int


@dataclass(frozen=True)
class OutputDeclNode(ASTNode):
    """Output dimension declaration (e.g. 'output: 10;')."""

    dim: int


@dataclass(frozen=True)
class DenseNode(ASTNode):
    """Fully connected Dense layer declaration."""

    in_features: int
    out_features: int
    weight_path: str
    bias_path: str


@dataclass(frozen=True)
class ActivationNode(ASTNode):
    """Activation function declaration ('ReLU' or 'Softmax')."""

    op: str  # "ReLU" or "Softmax"


LayerNode = DenseNode | ActivationNode


@dataclass(frozen=True)
class ModelNode(ASTNode):
    """Top-level neural network model definition."""

    name: str
    input_decl: InputDeclNode
    output_decl: OutputDeclNode
    layers: Sequence[LayerNode]


def format_ast(node: ASTNode, indent: int = 0) -> str:
    """Format an AST node hierarchy into a clean indented tree string."""
    prefix = "  " * indent
    if isinstance(node, ModelNode):
        lines = [
            f"{prefix}Model(name='{node.name}') at {node.line}:{node.col}",
            f"{prefix}  Input: {node.input_decl.dim} at {node.input_decl.line}:{node.input_decl.col}",
            f"{prefix}  Output: {node.output_decl.dim} at {node.output_decl.line}:{node.output_decl.col}",
            f"{prefix}  Layers ({len(node.layers)}):",
        ]
        for layer in node.layers:
            lines.append(format_ast(layer, indent + 2))
        return "\n".join(lines)

    if isinstance(node, DenseNode):
        return (
            f"{prefix}Dense(in={node.in_features}, out={node.out_features}, "
            f"w='{node.weight_path}', b='{node.bias_path}') at {node.line}:{node.col}"
        )

    if isinstance(node, ActivationNode):
        return f"{prefix}{node.op} at {node.line}:{node.col}"

    return f"{prefix}{type(node).__name__} at {node.line}:{node.col}"
