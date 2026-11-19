"""AST builder reduction actions for TMLC parser."""

from __future__ import annotations

from typing import Any

from tmlc.ast.nodes import (
    ActivationNode,
    DenseNode,
    InputDeclNode,
    LayerNode,
    ModelNode,
    OutputDeclNode,
)
from tmlc.lexer.lexer import Token


def reduce_action(prod_id: int, rhs: list[Any]) -> Any:
    """Execute semantic reduction action for a given production rule ID."""
    # 0: Start -> Model
    if prod_id == 0:
        return rhs[0]

    # 1: Model -> MODEL IDENT LBRACE ModelBody RBRACE
    if prod_id == 1:
        model_tok: Token = rhs[0]
        name_tok: Token = rhs[1]
        body_data: tuple[InputDeclNode, OutputDeclNode, list[LayerNode]] = rhs[3]
        return ModelNode(
            name=str(name_tok.value),
            input_decl=body_data[0],
            output_decl=body_data[1],
            layers=body_data[2],
            line=model_tok.line,
            col=model_tok.col,
        )

    # 2: ModelBody -> InputDecl OutputDecl LayerList
    if prod_id == 2:
        return (rhs[0], rhs[1], rhs[2])

    # 3: InputDecl -> INPUT COLON INT SEMICOLON
    if prod_id == 3:
        input_tok: Token = rhs[0]
        in_dim_tok: Token = rhs[2]
        return InputDeclNode(
            dim=int(in_dim_tok.value),
            line=input_tok.line,
            col=input_tok.col,
        )

    # 4: OutputDecl -> OUTPUT COLON INT SEMICOLON
    if prod_id == 4:
        output_tok: Token = rhs[0]
        out_dim_tok: Token = rhs[2]
        return OutputDeclNode(
            dim=int(out_dim_tok.value),
            line=output_tok.line,
            col=output_tok.col,
        )

    # 5: LayerList -> LayerList Layer
    if prod_id == 5:
        existing_list: list[LayerNode] = rhs[0]
        new_layer: LayerNode = rhs[1]
        return [*existing_list, new_layer]

    # 6: LayerList -> Layer
    if prod_id == 6:
        return [rhs[0]]

    # 7: Layer -> DenseLayer
    if prod_id == 7:
        return rhs[0]

    # 8: Layer -> ActivationLayer
    if prod_id == 8:
        return rhs[0]

    # 9: DenseLayer -> DENSE LPAREN INT COMMA INT COMMA STRING COMMA STRING RPAREN SEMICOLON
    if prod_id == 9:
        dense_tok: Token = rhs[0]
        in_dim: Token = rhs[2]
        out_dim: Token = rhs[4]
        w_path: Token = rhs[6]
        b_path: Token = rhs[8]
        return DenseNode(
            in_features=int(in_dim.value),
            out_features=int(out_dim.value),
            weight_path=str(w_path.value),
            bias_path=str(b_path.value),
            line=dense_tok.line,
            col=dense_tok.col,
        )

    # 10: ActivationLayer -> RELU SEMICOLON
    if prod_id == 10:
        relu_tok: Token = rhs[0]
        return ActivationNode(op="ReLU", line=relu_tok.line, col=relu_tok.col)

    # 11: ActivationLayer -> SOFTMAX SEMICOLON
    if prod_id == 11:
        softmax_tok: Token = rhs[0]
        return ActivationNode(op="Softmax", line=softmax_tok.line, col=softmax_tok.col)

    raise ValueError(f"Unknown production id: {prod_id}")
