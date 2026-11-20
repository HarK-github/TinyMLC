# TMLC Int8 Quantization Benchmark and Verification Results

This report compiles empirical results measured on **TMLC (TinyML Model-to-C Compiler)** for both the baseline float32 pipeline and the optional symmetric per-tensor int8 weight quantization pipeline.

Every numeric metric in this document was directly produced by commands and benchmarks executed during this verification process. No values are estimated or fabricated.

---

## 1. Summary Comparison Table

| Metric | Tiny Model (float32) | Tiny Model (int8) | MNIST Model (float32) | MNIST Model (int8) |
|---|---|---|---|---|
| **Architecture** | 4 $\to$ 8 $\to$ 2 | 4 $\to$ 8 $\to$ 2 | 784 $\to$ 128 $\to$ 64 $\to$ 10 | 784 $\to$ 128 $\to$ 64 $\to$ 10 |
| **Generated C Source Size** | 2,186 bytes | 1,947 bytes | 1,730,385 bytes | 484,444 bytes |
| **Weight Storage (Flash)** | 232 bytes | 96 bytes | 437,544 bytes (427.3 KB) | 110,004 bytes (107.4 KB) |
| **Storage Compression Ratio** | 1.00$\times$ (baseline) | 2.42$\times$ reduction | 1.00$\times$ (baseline) | **3.98$\times$ reduction** |
| **Working RAM (Ping-Pong)** | 40 bytes | 40 bytes | 768 bytes | 768 bytes |
| **Max Abs Error vs Reference** | 1.192093e-07 | 2.980232e-08 | 7.916242e-09 | 1.192093e-07 |
| **Verifier Result (atol=1e-5)** | **PASS** | **PASS** | **PASS** | **PASS** |
| **Inference Latency (PC, GCC -O2, cause not investigated, no claim for ESP32)** | N/A | N/A | 127.283 $\mu$s | **91.786 $\mu$s** |
| **Wokwi Simulated Latency** | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED |
| **Test Accuracy (10k MNIST)** | N/A | N/A | **97.68%** (9,768/10,000) | **97.67%** (9,767/10,000) |
| **Accuracy Delta** | N/A | N/A | Baseline | **-0.01 points** |
| **Prediction Agreement** | N/A | N/A | Baseline | **99.95%** |

---

## 2. Explanation of "NOT MEASURED" Entries

### Wokwi Simulated Inference Time
- **Status**: `NOT MEASURED`
- **Reason**: Simulation files (`sketch.ino`, `model.c`, `model.h`, `diagram.json`, `libraries.txt`, `README.md`) are prepared in `wokwi/` for ESP32-S3 (`board-esp32-s3-devkitc-1`), but have not been simulated. In this environment, only `model.c` was compiled on the host PC using GCC (`gcc -std=c99 -Wall -Wextra -Wpedantic -Werror -c model.c`); the Arduino sketch and simulation were not executed.

---

## 3. Detailed Per-Model Analysis

### A. Minimal Regression Model (`examples/tiny.tml`)
- **Pipeline Commands**:
  - Float32 generation: `python main.py generate examples/tiny.tml --out generated/`
  - Int8 generation: `python main.py generate examples/tiny.tml --quantize int8 --out generated_int8/`
  - Float32 verify: `python main.py verify examples/tiny.tml`
  - Int8 verify: `python main.py verify examples/tiny.tml --quantize int8`
- **Flash Memory Reduction**:
  - Float32: 58 parameters $\times$ 4 bytes = 232 bytes.
  - Int8: (32 int8 weights + 32 float bias + 4 float scale) + (16 int8 weights + 8 float bias + 4 float scale) = 96 bytes.
  - Reduction: **58.6% reduction in flash ROM footprint**.
- **Numerical Verification**:
  - Max absolute error against dequantized NumPy reference: $2.980232 \times 10^{-8} \le 1.0 \times 10^{-5}$ (`PASS`).

### B. MNIST Handwritten Digit Classifier (`examples/mnist.tml`)
- **Pipeline Commands**:
  - Float32 generation: `python main.py generate examples/mnist.tml --out generated/`
  - Int8 generation: `python main.py generate examples/mnist.tml --quantize int8 --out generated_int8/`
  - Float32 verify: `python main.py verify examples/mnist.tml`
  - Int8 verify: `python main.py verify examples/mnist.tml --quantize int8`
- **Flash Memory Reduction**:
  - Float32: 109,386 parameters $\times$ 4 bytes = 437,544 bytes (427.3 KB).
  - Int8: 109,184 int8 weights $\times$ 1 byte + 202 float biases $\times$ 4 bytes + 3 float scales $\times$ 4 bytes = 110,004 bytes (107.4 KB).
  - Reduction: **327,540 bytes saved (3.98$\times$ compression, 74.9% storage reduction)**.
- **Classification Accuracy on Real MNIST (`training/data/t10k`)**:
  - Evaluated on all 10,000 standard test partition images via `python tools/eval_accuracy.py` (int8 uses dequantized NumPy forward pass):
    - Float32: **97.68%** (9,768 / 10,000).
    - Int8 (dequantized weight forward pass): **97.67%** (9,767 / 10,000).
    - Accuracy delta: accuracy changed by 0.01 points (9,768 to 9,767); 5 of 10,000 predictions differ (99.95% agreement).
- **Execution Performance (PC, GCC -O2)**:
  - Float32 latency: 127.283 $\mu$s (measured on PC, GCC -O2, 10,000 calls).
  - Int8 latency: 91.786 $\mu$s (measured on PC, GCC -O2, 10,000 calls; cause not investigated, no claim for ESP32).
- **Numerical Verification**:
  - Max absolute error against dequantized NumPy reference across test vectors: $1.192093 \times 10^{-7} \le 1.0 \times 10^{-5}$ (`PASS`).
