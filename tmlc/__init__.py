"""TMLC: TinyML Model-to-C Compiler."""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from tmlc.errors import TmlcError

__all__ = ["TmlcError"]
