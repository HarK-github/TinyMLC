"""Pytest configuration and fixture hooks."""

from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import pathlib
import subprocess
import sys
import pytest


def assert_cli_build_fails(fixture_path: str | pathlib.Path, expected_code: str) -> None:
    """Run `main.py build` in a subprocess and assert non-zero exit, expected error code, and no model.c."""
    model_c = pathlib.Path("generated/model.c")
    if model_c.exists():
        model_c.unlink()

    res = subprocess.run(
        [sys.executable, "main.py", "build", str(fixture_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode != 0, f"Expected non-zero exit code for {fixture_path}, got 0"
    output = res.stderr + "\n" + res.stdout
    assert expected_code in output, f"Expected {expected_code} in CLI output for {fixture_path}:\n{output}"
    assert not model_c.exists(), f"generated/model.c must not exist after CLI build failure on {fixture_path}"


@pytest.fixture(autouse=True)
def clean_generated_model_c(request: pytest.FixtureRequest) -> None:
    """Ensure generated/model.c is removed before and after negative tests."""
    model_c = pathlib.Path("generated/model.c")
    # For tests asserting no model.c is written, ensure it is clean before the test starts
    if "test_codegen" not in request.node.nodeid and "test_verifier" not in request.node.nodeid:
        if model_c.exists():
            model_c.unlink()
    yield
