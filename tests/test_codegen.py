"""Tests for C99 code generation (Tests 1, 17, and forbidden call checks)."""

from __future__ import annotations

import math
import pathlib
import re
import subprocess

from tmlc.backend.c99 import C99Backend
from tmlc.ir.builder import build_ir
from tmlc.loader.weights import WeightLoader
from tmlc.optimizer.buffers import allocate_buffers
from tmlc.optimizer.fuse import fuse_dense_relu
from tmlc.parser.driver import ParserDriver
from tmlc.semantic.analyzer import SemanticAnalyzer


def test_test1_valid_mnist_codegen() -> None:
    """Test 1: Valid MNIST 784->128->64->10 is accepted and standalone C is generated."""
    driver = ParserDriver()
    ast = driver.parse_file("examples/mnist.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "examples")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)
    allocated_prog, report = allocate_buffers(fused_prog)

    out_dir = pathlib.Path("generated")
    backend = C99Backend()
    c_path, h_path = backend.generate(allocated_prog, report, out_dir=out_dir)

    assert c_path.is_file()
    assert h_path.is_file()
    assert c_path.stat().st_size > 1000

    # Compile with strict GCC flags
    res = subprocess.run(
        [
            "gcc",
            "-std=c99",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-c",
            str(c_path),
            "-o",
            str(out_dir / "model.o"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"GCC compilation failed:\n{res.stderr}"


def test_no_forbidden_calls_in_generated_c() -> None:
    """Verify generated C contains no malloc/calloc/free/file I/O."""
    model_c = pathlib.Path("generated/model.c")
    assert model_c.is_file()
    c_source = model_c.read_text(encoding="utf-8")

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
            f"Forbidden call '{fn}' found in generated/model.c"
        )


def test_test17_stable_softmax_large_logits() -> None:
    """Test 17: Softmax with large logits (+-1000) produces finite output summing to 1 within 1e-5."""
    driver = ParserDriver()
    ast = driver.parse_file("tests/fixtures/big_logits.tml")
    SemanticAnalyzer().analyze(ast)

    weights = WeightLoader().load_weights(ast, "tests/fixtures")
    ir_prog = build_ir(ast, weights)
    fused_prog = fuse_dense_relu(ir_prog)
    allocated_prog, report = allocate_buffers(fused_prog)

    out_dir = pathlib.Path("generated/test17")
    backend = C99Backend()
    c_path, _h_path = backend.generate(allocated_prog, report, out_dir=out_dir)

    # Build and run a small harness testing [1.0, 1.0] input
    harness_c = out_dir / "harness.c"
    harness_c.write_text(
        """#include <stdio.h>
#include <math.h>
#include "model.h"

int main() {
    float in[2] = {1.0f, 1.0f};
    float out[2];
    model_predict(in, out);
    printf("%.9g %.9g\\n", out[0], out[1]);
    return 0;
}
""",
        encoding="utf-8",
    )

    harness_exe = out_dir / "harness.exe"
    comp_res = subprocess.run(
        [
            "gcc",
            "-std=c99",
            "-I",
            str(out_dir),
            str(harness_c),
            str(c_path),
            "-o",
            str(harness_exe),
            "-lm",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert comp_res.returncode == 0, f"Compilation failed: {comp_res.stderr}"

    run_res = subprocess.run(
        [str(harness_exe)], check=False, capture_output=True, text=True
    )
    assert run_res.returncode == 0

    parts = [float(x) for x in run_res.stdout.strip().split()]
    assert len(parts) == 2
    # Output must be finite
    assert not any(math.isnan(v) or math.isinf(v) for v in parts)
    # Output must sum to 1 within 1e-5
    assert abs(sum(parts) - 1.0) <= 1e-5
