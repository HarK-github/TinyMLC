"""IR module for TMLC."""

from tmlc.ir.builder import IRProgram, build_ir
from tmlc.ir.ops import IROp, OpKind

__all__ = ["IROp", "IRProgram", "OpKind", "build_ir"]
