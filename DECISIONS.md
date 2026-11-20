# TMLC Project Decisions Log

## Confirmed Architectural Decisions

### 1. LR Table Construction (Confirmed: Option C)
- Implement **SLR(1) only**:
  - FIRST and FOLLOW computation.
  - LR(0) item sets, closure, and goto transitions.
  - SLR(1) ACTION and GOTO tables.
  - Shift/reduce driver supporting `--trace`.
- Keep table generation modular so CLR(1) and LALR(1) can be added later without refactoring.
- If the SLR(1) generator detects any shift/reduce or reduce/reduce conflicts on the grammar, **stop and report immediately** without rewriting grammar to hide conflicts.

### 2. Missing Input / Output Declarations (Tests 7 and 8)
- Confirmed: Missing input or output declarations are **`E101` parser syntax errors**.
- The grammar strictly enforces mandatory `InputDecl` and `OutputDecl` in `ModelBody`.

### 3. Dimension Validation (Test 9)
- Confirmed: Test dimension `0` (e.g., `Dense(0, 8, ...)`) for **`E202`** (non-positive dimension).
- Negative values (such as `-8`) are rejected at the lexer stage as **`E001`** (invalid character), since the lexer grammar has no minus sign token. A dedicated lexer test verifies this behavior.

### 4. Training Data & Dataset
- Confirmed: Attempt real MNIST first (784-128-64-10).
- If download fails or is unreachable, stop and report; do not silently switch to `sklearn.datasets.load_digits`.

### 5. Weight / Bias Path Strings
- Confirmed: An empty weight or bias path string (e.g., `""`) is treated as a missing file error (**`E301`**). No custom or redundant error code is introduced.

### 6. Symmetric Int8 Weight-Only Quantization (Optional Stage)
- **Scope & Quantization Scheme**:
  - Implement optional symmetric per-tensor int8 weight-only quantization: $\text{scale} = \max(|W|) / 127.0$, $q = \text{clip}(\text{round}(W / \text{scale}), -127, 127)$.
  - Keep activations and bias vectors in float32. No zero points, no per-channel quantization, no activation quantization, and no requantization.
  - Zero-weight edge case explicitly defined: if $\max(|W|) == 0.0$, $\text{scale} = 1.0f$, keeping scale positive and finite.
- **Verification Oracle**:
  - Independent NumPy reference reconstructs dequantized weights: $W_{\text{dequant}} = q \cdot \text{scale}$.
  - Compiled C output is compared against $W_{\text{dequant}}$ under existing tolerance ($\text{atol}=10^{-5}, \text{rtol}=10^{-4}$). Unquantized float32 weights are never compared against int8 output for verification.
- **CLI & Output Separation**:
  - Default CLI remains unquantized float32.
  - Flag `--quantize int8` directs output to `generated_int8/` by default, strictly preventing overwriting `generated/`.
- **Wokwi Embedded Simulation**:
  - ESP32-S3 simulation files (`board-esp32-s3-devkitc-1`) are prepared in `wokwi/` for the Tiny model via Serial Monitor input with `micros()` timing, but have not been simulated. Only `model.c` was compiled on the host PC using GCC.
  - Reports explicitly distinguish prepared simulation files from simulated execution and physical hardware deployment.
