"""Static buffer allocation and memory analysis for TinyML models."""

from __future__ import annotations

from dataclasses import dataclass

from tmlc.ir.builder import IRProgram
from tmlc.ir.ops import IROp, OpKind


@dataclass(frozen=True)
class MemoryReport:
    """Static memory consumption report for microcontroller deployment."""

    model_name: str
    param_count: int
    flash_weight_bytes: int
    buffer_a_floats: int
    buffer_a_bytes: int
    buffer_b_floats: int
    buffer_b_bytes: int
    total_ram_bytes: int
    layer_details: list[str]

    def format(self) -> str:
        """Format memory report matching build plan requirements."""
        lines = [
            "============================================================",
            f"          STATIC MEMORY REPORT: {self.model_name}",
            "============================================================",
            "FLASH STORAGE (STATIC CONST WEIGHTS & BIASES):",
            f"  Total Parameters     : {self.param_count:,} floats",
            f"  Flash Weight Storage : {self.flash_weight_bytes:,} Bytes ({self.flash_weight_bytes / 1024:.2f} KB)",
            "------------------------------------------------------------",
            "RAM ALLOCATION (TWO STATIC WORKING BUFFERS):",
            f"  Buffer A (Primary)   : {self.buffer_a_floats} floats ({self.buffer_a_bytes} Bytes)",
            f"  Buffer B (Secondary) : {self.buffer_b_floats} floats ({self.buffer_b_bytes} Bytes)",
            f"  Total Working RAM    : {self.total_ram_bytes} Bytes ({self.total_ram_bytes / 1024:.2f} KB)",
            "------------------------------------------------------------",
            "PER-LAYER SPECIFICATIONS:",
        ]
        for detail in self.layer_details:
            lines.append(f"  * {detail}")
        lines.append("------------------------------------------------------------")
        lines.append("ZERO DYNAMIC ALLOCATION: No malloc/calloc/free required.")
        lines.append("============================================================")
        return "\n".join(lines)


def allocate_buffers(program: IRProgram) -> tuple[IRProgram, MemoryReport]:
    """Assign static ping-pong buffers (buf_a, buf_b) to IR operations and compute memory."""
    new_ops: list[IROp] = []
    layer_details: list[str] = []

    total_params = 0
    buf_a_needed = 0
    buf_b_needed = 0

    current_src = "input"
    next_buf = "buf_a"

    for op in program.ops:
        if op.kind == OpKind.INPUT:
            # Input op passes caller input buffer
            assigned_op = IROp(
                kind=op.kind,
                in_dim=op.in_dim,
                out_dim=op.out_dim,
                input_buf="input",
                output_buf="input",
            )
            new_ops.append(assigned_op)
            current_src = "input"
            next_buf = "buf_a"

        elif op.kind in (OpKind.DENSE, OpKind.DENSE_RELU):
            w_params = (op.in_dim * op.out_dim) if op.weights is not None else 0
            b_params = op.out_dim if op.bias is not None else 0
            layer_params = w_params + b_params
            total_params += layer_params

            dst_buf = next_buf
            if dst_buf == "buf_a":
                buf_a_needed = max(buf_a_needed, op.out_dim)
                next_buf = "buf_b"
            else:
                buf_b_needed = max(buf_b_needed, op.out_dim)
                next_buf = "buf_a"

            assigned_op = IROp(
                kind=op.kind,
                in_dim=op.in_dim,
                out_dim=op.out_dim,
                weights=op.weights,
                bias=op.bias,
                input_buf=current_src,
                output_buf=dst_buf,
            )
            new_ops.append(assigned_op)
            current_src = dst_buf
            layer_details.append(
                f"{op.kind.value}({op.in_dim} -> {op.out_dim}): "
                f"{layer_params:,} params ({layer_params * 4:,} B) [{assigned_op.input_buf} -> {assigned_op.output_buf}]"
            )

        elif op.kind in (OpKind.RELU, OpKind.SOFTMAX):
            # In-place or same buffer transform
            assigned_op = IROp(
                kind=op.kind,
                in_dim=op.in_dim,
                out_dim=op.out_dim,
                input_buf=current_src,
                output_buf=current_src,
            )
            new_ops.append(assigned_op)
            layer_details.append(
                f"{op.kind.value}({op.in_dim}): in-place on {current_src}"
            )

        elif op.kind == OpKind.OUTPUT:
            assigned_op = IROp(
                kind=op.kind,
                in_dim=op.in_dim,
                out_dim=op.out_dim,
                input_buf=current_src,
                output_buf="output",
            )
            new_ops.append(assigned_op)

    flash_weight_bytes = total_params * 4
    buf_a_bytes = buf_a_needed * 4
    buf_b_bytes = buf_b_needed * 4
    total_ram_bytes = buf_a_bytes + buf_b_bytes

    report = MemoryReport(
        model_name=program.name,
        param_count=total_params,
        flash_weight_bytes=flash_weight_bytes,
        buffer_a_floats=buf_a_needed,
        buffer_a_bytes=buf_a_bytes,
        buffer_b_floats=buf_b_needed,
        buffer_b_bytes=buf_b_bytes,
        total_ram_bytes=total_ram_bytes,
        layer_details=layer_details,
    )

    allocated_program = IRProgram(
        name=program.name,
        input_dim=program.input_dim,
        output_dim=program.output_dim,
        ops=new_ops,
    )

    return allocated_program, report
