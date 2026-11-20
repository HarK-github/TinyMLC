# TMLC Symmetric Int8 Weight-Only Quantization

TMLC provides an optional ahead-of-time **symmetric per-tensor int8 weight-only quantization** pipeline designed specifically for microcontroller deployment with constrained flash (ROM) storage.

---

## 1. Mathematical Formulation

### Quantization Pass
For each Dense weight tensor $W \in \mathbb{R}^{M \times N}$:
1. Compute the per-tensor dynamic scale:
   $$\text{scale} = \begin{cases} \frac{\max(|W|)}{127.0} & \text{if } \max(|W|) > 0 \\ 1.0 & \text{if } \max(|W|) = 0 \end{cases}$$
2. Round and clip each weight value into the symmetric 8-bit signed integer range $[-127, 127]$:
   $$q = \text{clip}\left(\left\lfloor \frac{W}{\text{scale}} \right\rceil, -127, 127\right) \in \mathbb{Z}^{M \times N}$$

- Quantized weights $q$ are stored as `static const int8_t`.
- The scale factor $\text{scale}$ is stored as a `static const float`.
- Biases remain unquantized as `static const float` (float32).
- Intermediate activations and working buffers remain in single precision float32.

### Dequantization Reference & Verification
To ensure mathematical fidelity, the independent NumPy verification oracle reconstructs the effective floating-point weights:
$$W_{\text{dequant}} = q \cdot \text{scale}$$
Inference is executed using $W_{\text{dequant}}$, and compiled C output is compared against this reference under strict numerical tolerances:
$$\text{atol} = 10^{-5}, \quad \text{rtol} = 10^{-4}$$

---

## 2. Generated C Inner Loop Architecture

In the generated C99 source code, linear Dense accumulation is performed directly in single-precision floating-point arithmetic by dequantizing on-the-fly during multiply-accumulate:

```c
/* Fused Dense+ReLU(in_dim -> out_dim) [int8 quantized] */
for (int i = 0; i < out_dim; i++) {
    float acc = 0.0f;
    for (int j = 0; j < in_dim; j++) {
        acc += input[j] * ((float)layer_weights[j * out_dim + i] * layer_scale);
    }
    acc += layer_bias[i];
    output[i] = (acc > 0.0f) ? acc : 0.0f;
}
```

### Architectural Guarantees
- **Strict ANSI C99 compliance**: Compiles with GCC using `-Wall -Wextra -Wpedantic -Werror`.
- **Zero dynamic memory allocation**: No `malloc`, `calloc`, `realloc`, or `free`.
- **Zero external runtime dependencies**: Standalone standard library math (`expf`) only.
- **Symmetric range**: Values strictly stay within $[-127, 127]$, preventing asymmetrical overflow at $-128$.

---

## 3. Command-Line Interface (CLI)

### Default (Unquantized Float32)
```bash
# Generate float32 model into generated/
python main.py generate examples/mnist.tml --out generated/

# Verify float32 model
python main.py verify examples/mnist.tml
```

### Quantized Int8 Pipeline
```bash
# Generate int8 model into generated_int8/
python main.py generate examples/mnist.tml --quantize int8 --out generated_int8/

# Verify int8 model against dequantized NumPy reference
python main.py verify examples/mnist.tml --quantize int8

# Display static memory report showing int8 flash savings
python main.py memory examples/mnist.tml --quantize int8

# Inspect IR with quantization metadata
python main.py ir examples/mnist.tml --opt --quantize int8
```

---

## 4. Empirical Evaluation

### Memory Footprint Comparison

| Model | Parameter Count | Float32 Weight Flash | Int8 Weight Flash | Compression Ratio | Working RAM |
|---|---|---|---|---|---|
| **Tiny** (4-8-2) | 58 | 232 B | 96 B | **2.42$\times$** | 40 B |
| **MNIST** (784-128-64-10) | 109,386 | 437,544 B (427.3 KB) | 110,004 B (107.4 KB) | **3.98$\times$** | 768 B |

### Numerical Accuracy & Verification

- **MNIST Classification Accuracy**:
  - Float32 baseline: **97.68%** (9,768 / 10,000 test set).
  - Int8 weight-only: **97.67%** (9,767 / 10,000 test set; evaluated using the dequantized NumPy forward pass via `python tools/eval_accuracy.py`).
  - Accuracy delta: accuracy changed by 0.01 points (9,768 to 9,767); 5 of 10,000 predictions differ (99.95% agreement).
- **Numerical Verification Error**:
  - Tiny model max absolute error: $2.98 \times 10^{-8} \le 1.0 \times 10^{-5}$ (`PASS`).
  - MNIST model max absolute error: $1.19 \times 10^{-7} \le 1.0 \times 10^{-5}$ (`PASS`).

---

## 5. ESP32-S3 Wokwi Simulation

Simulation files targeting the ESP32-S3 (`board-esp32-s3-devkitc-1`) are prepared in the `wokwi/` directory, but have not been simulated. On the host PC, `wokwi/model.c` was compiled with GCC (`gcc -std=c99 -Wall -Wextra -Wpedantic -Werror -c model.c`).

- Embedded model: Tiny (4 $\to$ 8 $\to$ 2) int8 quantized (`model.c`, `model.h`).
- Interface: Serial Monitor (115200 baud).
- Input: Comma-separated floating point values (e.g. `0.5, -0.2, 0.8, -0.4`).
- Output: Predicted class, inference latency in microseconds (`micros()`), raw output vector.
