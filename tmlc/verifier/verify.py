"""Independent model verifier comparing GCC-compiled C output against NumPy reference."""

from __future__ import annotations

import pathlib
import subprocess
from collections.abc import Sequence

import numpy as np

from tmlc.ast.nodes import ActivationNode, DenseNode
from tmlc.backend.c99 import C99Backend, format_c_float
from tmlc.errors import TmlcError
from tmlc.ir.builder import build_ir
from tmlc.loader.weights import WeightLoader
from tmlc.optimizer.buffers import allocate_buffers
from tmlc.optimizer.fuse import fuse_dense_relu
from tmlc.parser.driver import ParserDriver
from tmlc.semantic.analyzer import SemanticAnalyzer


class ModelVerifier:
    """Verifies generated C99 code against an independent NumPy reference implementation."""

    def numpy_reference_predict(
        self,
        tml_path: str | pathlib.Path,
        input_vector: np.ndarray,
    ) -> np.ndarray:
        """Independent NumPy reference inference engine.

        Loads weights directly from disk without touching backend code or IR buffers.
        """
        p = pathlib.Path(tml_path)
        base_dir = p.parent
        ast = ParserDriver().parse_file(p)

        curr = input_vector.astype(np.float32).flatten()
        assert len(curr) == ast.input_decl.dim, (
            f"Input vector length {len(curr)} != {ast.input_decl.dim}"
        )

        for layer in ast.layers:
            if isinstance(layer, DenseNode):
                w_file = (base_dir / layer.weight_path).resolve()
                b_file = (base_dir / layer.bias_path).resolve()
                w = np.load(w_file).astype(np.float32)
                b = np.load(b_file).astype(np.float32).flatten()

                # Dot product matching C loop order: out[i] = sum(in[j] * w[j, i]) + b[i]
                curr = curr @ w + b

            elif isinstance(layer, ActivationNode):
                if layer.op == "ReLU":
                    curr = np.maximum(curr, 0.0)
                elif layer.op == "Softmax":
                    max_val = np.max(curr)
                    exp_val = np.exp(curr - max_val)
                    curr = exp_val / np.sum(exp_val)

        return curr.astype(np.float32)

    def _compile_and_run_c(
        self,
        c_path: pathlib.Path,
        h_path: pathlib.Path,
        input_vector: np.ndarray,
        out_dim: int,
        out_dir: pathlib.Path,
    ) -> np.ndarray:
        """Compile generated C99 source with GCC and execute single inference."""
        if not c_path.is_file() or not h_path.is_file():
            raise TmlcError("E602", f"Generated C source or header missing at {c_path}")

        out_dir.mkdir(parents=True, exist_ok=True)
        harness_c = out_dir / "verify_harness.c"
        harness_exe = out_dir / "verify_harness.exe"

        in_floats_str = ", ".join(
            format_c_float(float(x)) for x in input_vector.flatten()
        )
        harness_code = f"""#include <stdio.h>
#include "model.h"

int main(void) {{
    const float in[MODEL_INPUT_DIM] = {{ {in_floats_str} }};
    float out[MODEL_OUTPUT_DIM];
    model_predict(in, out);
    for (int i = 0; i < MODEL_OUTPUT_DIM; i++) {{
        printf("%.9g\\n", out[i]);
    }}
    return 0;
}}
"""
        harness_c.write_text(harness_code, encoding="utf-8")

        # Compile with GCC
        cmd_compile = [
            "gcc",
            "-std=c99",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-I",
            str(out_dir),
            "-I",
            str(c_path.parent),
            str(harness_c),
            str(c_path),
            "-o",
            str(harness_exe),
            "-lm",
        ]

        try:
            comp_res = subprocess.run(cmd_compile, check=False, capture_output=True, text=True)
        except FileNotFoundError as ex:
            raise TmlcError("E602", f"GCC not found on system: {ex}") from ex

        if comp_res.returncode != 0:
            raise TmlcError("E602", f"GCC compilation failed:\n{comp_res.stderr}")

        # Run compiled binary
        try:
            run_res = subprocess.run([str(harness_exe)], check=False, capture_output=True, text=True)
        except Exception as ex:
            raise TmlcError(
                "E602", f"Execution of compiled C binary failed: {ex}"
            ) from ex

        if run_res.returncode != 0:
            raise TmlcError(
                "E602",
                f"Compiled C binary exited with code {run_res.returncode}:\n{run_res.stderr}",
            )

        parts = [
            float(line.strip())
            for line in run_res.stdout.strip().split()
            if line.strip()
        ]
        if len(parts) != out_dim:
            raise TmlcError(
                "E601", f"C binary produced {len(parts)} outputs, expected {out_dim}"
            )

        return np.array(parts, dtype=np.float32)

    def verify_model(
        self,
        tml_path: str | pathlib.Path,
        input_vectors: Sequence[np.ndarray] | None = None,
        out_dir: str | pathlib.Path = "generated",
    ) -> tuple[float, bool]:
        """Perform full end-to-end compilation and numerical verification.

        Compares output against independent NumPy baseline with atol=1e-5, rtol=1e-4.

        Raises:
            TmlcError: E601 if numerical output differs, E602 if gcc fails.
        """
        p = pathlib.Path(tml_path)
        base_dir = p.parent
        dest = pathlib.Path(out_dir)

        # 1. Compile pipeline to generate C
        driver = ParserDriver()
        ast = driver.parse_file(p)
        SemanticAnalyzer().analyze(ast)

        weights = WeightLoader().load_weights(ast, base_dir)
        ir_prog = build_ir(ast, weights)
        fused_prog = fuse_dense_relu(ir_prog)
        allocated_prog, report = allocate_buffers(fused_prog)

        backend = C99Backend()
        c_path, h_path = backend.generate(allocated_prog, report, out_dir=dest)

        # 2. Determine input vectors
        if input_vectors is None or len(input_vectors) == 0:
            test_inputs_file = base_dir / "test_inputs.npy"
            if test_inputs_file.is_file():
                loaded_inputs = np.load(test_inputs_file)
                if (
                    len(loaded_inputs.shape) == 2
                    and loaded_inputs.shape[1] == ast.input_decl.dim
                ):
                    test_vecs: list[np.ndarray] = list(loaded_inputs[:5])
                else:
                    rng = np.random.default_rng(seed=123)
                    test_vecs = [
                        rng.uniform(-1.0, 1.0, ast.input_decl.dim).astype(np.float32)
                        for _ in range(5)
                    ]
            else:
                rng = np.random.default_rng(seed=123)
                test_vecs = [
                    rng.uniform(-1.0, 1.0, ast.input_decl.dim).astype(np.float32)
                    for _ in range(5)
                ]
        else:
            test_vecs = list(input_vectors)

        max_error = 0.0

        for idx, vec in enumerate(test_vecs, 1):
            c_out = self._compile_and_run_c(
                c_path=c_path,
                h_path=h_path,
                input_vector=vec,
                out_dim=ast.output_decl.dim,
                out_dir=dest,
            )

            np_out = self.numpy_reference_predict(p, vec)

            diff = np.abs(c_out - np_out)
            vec_max_err = float(np.max(diff))
            max_error = max(max_error, vec_max_err)

            # Strict numerical check with atol=1e-5, rtol=1e-4
            if not np.allclose(c_out, np_out, atol=1e-5, rtol=1e-4):
                raise TmlcError(
                    "E601",
                    f"Vector {idx} verification failed: max abs error {vec_max_err:.6e} "
                    f"exceeds tolerance (atol=1e-5, rtol=1e-4)",
                )

        print(
            f"PASS: Verified {len(test_vecs)} input vectors on model '{ast.name}' "
            f"(max absolute error: {max_error:.2e} <= 1e-5)"
        )
        return max_error, True
