"""Pytest configuration and fixture hooks."""

from __future__ import annotations

import pathlib
import pytest


@pytest.fixture(autouse=True)
def clean_generated_model_c(request: pytest.FixtureRequest) -> None:
    """Ensure generated/model.c is removed before and after negative tests."""
    model_c = pathlib.Path("generated/model.c")
    # For tests asserting no model.c is written, ensure it is clean before the test starts
    if "test_codegen" not in request.node.nodeid and "test_verifier" not in request.node.nodeid:
        if model_c.exists():
            model_c.unlink()
    yield
