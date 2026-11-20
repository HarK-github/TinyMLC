"""C99 code templates for neural network operators."""

from __future__ import annotations


def dense_loop_c(
    in_dim: int, out_dim: int, w_name: str, b_name: str, src: str, dst: str
) -> str:
    """Generate C nested loops for standard linear Dense transform."""
    return f"""    /* Dense({in_dim} -> {out_dim}): {src} to {dst} */
    for (int i = 0; i < {out_dim}; i++) {{
        float sum = {b_name}[i];
        for (int j = 0; j < {in_dim}; j++) {{
            sum += {src}[j] * {w_name}[j * {out_dim} + i];
        }}
        {dst}[i] = sum;
    }}"""


def dense_relu_loop_c(
    in_dim: int, out_dim: int, w_name: str, b_name: str, src: str, dst: str
) -> str:
    """Generate C nested loops for fused Dense + ReLU transform."""
    return f"""    /* Fused Dense+ReLU({in_dim} -> {out_dim}): {src} to {dst} */
    for (int i = 0; i < {out_dim}; i++) {{
        float sum = {b_name}[i];
        for (int j = 0; j < {in_dim}; j++) {{
            sum += {src}[j] * {w_name}[j * {out_dim} + i];
        }}
        {dst}[i] = (sum > 0.0f) ? sum : 0.0f;
    }}"""


def dense_loop_int8_c(
    in_dim: int,
    out_dim: int,
    w_name: str,
    b_name: str,
    scale_name: str,
    src: str,
    dst: str,
) -> str:
    """Generate C nested loops for int8 quantized linear Dense transform."""
    return f"""    /* Dense({in_dim} -> {out_dim}): {src} to {dst} [int8 quantized] */
    for (int i = 0; i < {out_dim}; i++) {{
        float acc = 0.0f;
        for (int j = 0; j < {in_dim}; j++) {{
            acc += {src}[j] * ((float){w_name}[j * {out_dim} + i] * {scale_name});
        }}
        acc += {b_name}[i];
        {dst}[i] = acc;
    }}"""


def dense_relu_loop_int8_c(
    in_dim: int,
    out_dim: int,
    w_name: str,
    b_name: str,
    scale_name: str,
    src: str,
    dst: str,
) -> str:
    """Generate C nested loops for int8 quantized fused Dense + ReLU transform."""
    return f"""    /* Fused Dense+ReLU({in_dim} -> {out_dim}): {src} to {dst} [int8 quantized] */
    for (int i = 0; i < {out_dim}; i++) {{
        float acc = 0.0f;
        for (int j = 0; j < {in_dim}; j++) {{
            acc += {src}[j] * ((float){w_name}[j * {out_dim} + i] * {scale_name});
        }}
        acc += {b_name}[i];
        {dst}[i] = (acc > 0.0f) ? acc : 0.0f;
    }}"""


def relu_loop_c(dim: int, buf: str) -> str:
    """Generate C in-place loop for ReLU activation."""
    return f"""    /* ReLU({dim}): in-place on {buf} */
    for (int i = 0; i < {dim}; i++) {{
        if ({buf}[i] < 0.0f) {{
            {buf}[i] = 0.0f;
        }}
    }}"""


def softmax_loop_c(dim: int, src: str, dst: str) -> str:
    """Generate numerically stable Softmax using max-subtraction."""
    return f"""    /* Numerically stable Softmax({dim}): {src} to {dst} */
    {{
        float max_val = {src}[0];
        for (int i = 1; i < {dim}; i++) {{
            if ({src}[i] > max_val) {{
                max_val = {src}[i];
            }}
        }}
        float sum_exp = 0.0f;
        for (int i = 0; i < {dim}; i++) {{
            {dst}[i] = expf({src}[i] - max_val);
            sum_exp += {dst}[i];
        }}
        float inv_sum = 1.0f / sum_exp;
        for (int i = 0; i < {dim}; i++) {{
            {dst}[i] *= inv_sum;
        }}
    }}"""
