"""Tests for TMLC IR builder, operator fusion, and static buffer allocation."""

from __future__ import annotations

import pytest

from tmlc.errors import TmlcError
from tmlc.ir.builder import build_ir
from tmlc.ir.ops import IROp, OpKind
from tmlc.loader.weights import WeightLoader
from tmlc.optimizer.buffers import allocate_buffers
from tmlc.optimizer.fuse import fuse_dense_relu
from tmlc.parser.driver import ParserDriver
from tmlc.semantic.analyzer import SemanticAnalyzer


def test_tiny_ir_and_fusion() -> None:
    """Test IR construction and fusion for tiny.tml."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/tiny.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)

    # tiny.tml: INPUT, DENSE, RELU, DENSE, OUTPUT -> 5 ops
    assert len(ir_prog.ops) == 5
    assert [op.kind for op in ir_prog.ops] == [
        OpKind.INPUT,
        OpKind.DENSE,
        OpKind.RELU,
        OpKind.DENSE,
        OpKind.OUTPUT,
    ]

    fused_prog = fuse_dense_relu(ir_prog)
    # After fusion: INPUT, DENSE_RELU, DENSE, OUTPUT -> 4 ops
    assert len(fused_prog.ops) == 4
    assert [op.kind for op in fused_prog.ops] == [
        OpKind.INPUT,
        OpKind.DENSE_RELU,
        OpKind.DENSE,
        OpKind.OUTPUT,
    ]


def test_mnist_ir_and_fusion_op_counts() -> None:
    """Exit check: mnist.tml IR has 8 ops before fusion and 6 ops after."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/mnist.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    assert len(ir_prog.ops) == 8

    fused_prog = fuse_dense_relu(ir_prog)
    assert len(fused_prog.ops) == 6

    op_kinds = [op.kind for op in fused_prog.ops]
    assert op_kinds == [
        OpKind.INPUT,
        OpKind.DENSE_RELU,
        OpKind.DENSE_RELU,
        OpKind.DENSE,
        OpKind.SOFTMAX,
        OpKind.OUTPUT,
    ]


def test_mnist_memory_allocation_report() -> None:
    """Exit check: memory prints 437,544 weight bytes and 768 working buffer bytes."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/mnist.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)
    _, report = allocate_buffers(fused_prog)

    assert report.param_count == 109386
    assert report.flash_weight_bytes == 437544
    assert report.buffer_a_floats == 128
    assert report.buffer_a_bytes == 512
    assert report.buffer_b_floats == 64
    assert report.buffer_b_bytes == 256
    assert report.total_ram_bytes == 768


def test_ir_shape_inconsistency_e401() -> None:
    """Operator fusion catches shape inconsistency with E401."""
    from tmlc.ir.builder import IRProgram

    invalid_prog = IRProgram(
        name="BadProg",
        input_dim=10,
        output_dim=10,
        ops=[
            IROp(kind=OpKind.DENSE, in_dim=10, out_dim=20),
            IROp(kind=OpKind.RELU, in_dim=30, out_dim=30),  # Mismatch: 20 vs 30
        ],
    )

    with pytest.raises(TmlcError) as exc_info:
        fuse_dense_relu(invalid_prog)

    err = exc_info.value
    assert err.code == "E401"
