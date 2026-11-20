"""Tests for C99 code generation with int8 weight quantization."""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

from tmlc.backend.c99 import C99Backend
from tmlc.ir.builder import build_ir
from tmlc.loader.weights import WeightLoader
from tmlc.optimizer.buffers import allocate_buffers
from tmlc.optimizer.fuse import fuse_dense_relu
from tmlc.parser.driver import ParserDriver
from tmlc.quantization.int8 import quantize_ir
from tmlc.semantic.analyzer import SemanticAnalyzer


def test_generated_c_contains_int8_arrays() -> None:
    """Verify generated C contains int8_t weight arrays and float scale factors."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/tiny.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)
    quant_prog = quantize_ir(fused_prog)
    allocated_prog, report = allocate_buffers(quant_prog)

    out_dir = pathlib.Path("generated_int8/test_tiny")
    backend = C99Backend()
    c_path, h_path = backend.generate(allocated_prog, report, out_dir=out_dir)

    assert c_path.is_file()
    assert h_path.is_file()

    c_source = c_path.read_text(encoding="utf-8")
    h_source = h_path.read_text(encoding="utf-8")

    # Header must define standard MCU macros
    assert "#define MODEL_INPUT_SIZE MODEL_INPUT_DIM" in h_source
    assert "#define MODEL_OUTPUT_SIZE MODEL_OUTPUT_DIM" in h_source
    assert "#include <stdint.h>" in h_source or "#include <stdint.h>" in c_source

    # Source must define static const int8_t weights and float scale
    assert re.search(r"static\s+const\s+int8_t\s+layer1_weights\[\d+\]\s*=", c_source)
    assert re.search(r"static\s+const\s+float\s+layer1_scale\s*=", c_source)
    assert re.search(r"static\s+const\s+float\s+layer1_bias\[\d+\]\s*=", c_source)


def test_generated_c_no_dynamic_allocation_or_forbidden_calls() -> None:
    """Verify generated int8 C contains no malloc/calloc/free/realloc/file I/O."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/mnist.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)
    quant_prog = quantize_ir(fused_prog)
    allocated_prog, report = allocate_buffers(quant_prog)

    out_dir = pathlib.Path("generated_int8/test_forbidden")
    backend = C99Backend()
    c_path, _ = backend.generate(allocated_prog, report, out_dir=out_dir)

    c_source = c_path.read_text(encoding="utf-8")
    forbidden = [
        "malloc",
        "calloc",
        "free",
        "realloc",
        "fopen",
        "fclose",
        "fread",
        "fwrite",
        "printf",
        "fprintf",
    ]
    for fn in forbidden:
        pattern = rf"\b{fn}\s*\("
        assert not re.search(pattern, c_source), (
            f"Forbidden call '{fn}' found in generated int8 C source"
        )


def test_generated_c_compiles_with_gcc() -> None:
    """Verify generated int8 C compiles cleanly under strict ANSI C99 GCC flags."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/tiny.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)
    quant_prog = quantize_ir(fused_prog)
    allocated_prog, report = allocate_buffers(quant_prog)

    out_dir = pathlib.Path("generated_int8/test_compile")
    backend = C99Backend()
    c_path, _ = backend.generate(allocated_prog, report, out_dir=out_dir)

    obj_path = out_dir / "model.o"
    cmd = [
        "gcc",
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-Wpedantic",
        "-Werror",
        "-c",
        str(c_path),
        "-o",
        str(obj_path),
    ]
    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    assert res.returncode == 0, f"GCC compilation failed:\n{res.stderr}"
    assert obj_path.is_file()


def test_default_float32_path_remains_unchanged() -> None:
    """Verify default generation without --quantize produces pure float32 arrays."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/tiny.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)
    allocated_prog, report = allocate_buffers(fused_prog)

    out_dir = pathlib.Path("generated/test_f32_check")
    backend = C99Backend()
    c_path, _ = backend.generate(allocated_prog, report, out_dir=out_dir)

    c_source = c_path.read_text(encoding="utf-8")
    assert re.search(r"static\s+const\s+float\s+layer1_weights\[\d+\]\s*=", c_source)
    assert "int8_t" not in c_source
    assert "layer1_scale" not in c_source


def test_invalid_quantize_arg_produces_nonzero_diagnostic() -> None:
    """CLI exits non-zero and prints diagnostic when an invalid quantization mode is given."""
    # 1. Invalid generate flag
    res_gen = subprocess.run(
        [
            sys.executable,
            "main.py",
            "generate",
            "examples/tiny.tml",
            "--quantize",
            "invalid_mode",
            "--out",
            "generated_int8/tmp",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert res_gen.returncode != 0
    assert "Unsupported quantization mode" in res_gen.stderr

    # 2. Invalid verify flag
    res_ver = subprocess.run(
        [
            sys.executable,
            "main.py",
            "verify",
            "examples/tiny.tml",
            "--quantize",
            "fp16",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert res_ver.returncode != 0
    assert "Unsupported quantization mode" in res_ver.stderr


def test_int8_inner_loop_accumulation_expression() -> None:
    """Verify inner loop explicitly computes acc += x[k] * ((float)w_q[k] * scale)."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/tiny.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)
    quant_prog = quantize_ir(fused_prog)
    allocated_prog, report = allocate_buffers(quant_prog)

    out_dir = pathlib.Path("generated_int8/test_loop_expr")
    backend = C99Backend()
    c_path, _ = backend.generate(allocated_prog, report, out_dir=out_dir)

    c_source = c_path.read_text(encoding="utf-8")
    pattern = r"acc\s*\+=\s*input\[j\]\s*\*\s*\(\(float\)layer1_weights\[j\s*\*\s*8\s*\+\s*i\]\s*\*\s*layer1_scale\);"
    assert re.search(pattern, c_source), (
        "Inner loop does not match expected accumulation expression acc += x * ((float)w * scale)"
    )
