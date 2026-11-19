"""Optimizer module for TMLC."""

from tmlc.optimizer.buffers import MemoryReport, allocate_buffers
from tmlc.optimizer.fuse import fuse_dense_relu

__all__ = ["MemoryReport", "allocate_buffers", "fuse_dense_relu"]
