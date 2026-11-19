# TMLC: TinyML Model-to-C Compiler

TMLC is an ahead-of-time compiler that transforms deep neural network models specified in `.tml` files with `.npy` weight matrices into self-contained, dependency-free ANSI C99 source code suitable for microcontroller deployment.

## Prerequisites

- **Python**: 3.10+ (tested on Python 3.13)
- **C Compiler**: GCC supporting `-std=c99` (e.g., GCC 14.2)
- **Make**: GNU Make (optional, for automation)

## Setup

```bash
git clone <repo-url>
cd TinyMLproject
pip install -r requirements.txt
```

## Quick Start & Demo Sequence

1. **Inspect Token Stream**:
   ```bash
   python main.py tokens examples/mnist.tml
   ```

2. **Parse Model with Shift/Reduce Trace**:
   ```bash
   python main.py parse examples/mnist.tml --trace
   ```

3. **Inspect SLR(1) Parsing Tables and Conflict Counts**:
   ```bash
   python main.py tables
   ```

4. **Display Abstract Syntax Tree**:
   ```bash
   python main.py ast examples/mnist.tml
   ```

5. **Run Semantic Analysis**:
   ```bash
   python main.py semantic examples/mnist.tml
   ```

6. **Generate and Optimize Intermediate Representation (IR)**:
   ```bash
   python main.py ir examples/mnist.tml --opt
   ```

7. **Display Static Memory Allocation Report**:
   ```bash
   python main.py memory examples/mnist.tml
   ```

8. **Build Standalone C99 Source and Header**:
   ```bash
   python main.py build examples/mnist.tml
   ```

9. **Verify Numerical Output Against NumPy Reference**:
   ```bash
   python main.py verify examples/mnist.tml
   ```

## Diagnostic Error Codes

| Code | Stage | Description |
| --- | --- | --- |
| E001 | Lexer | Invalid character |
| E002 | Lexer | Unterminated string |
| E101 | Parser | Unexpected token / syntax error |
| E201 | Semantic | Layer dimension mismatch |
| E202 | Semantic | Non-positive dimension |
| E203 | Semantic | Last Dense output differs from output declaration |
| E204 | Semantic | Model has no Dense layer |
| E301 | Loader | Missing weight or bias file (or empty path) |
| E302 | Loader | Weight shape mismatch |
| E303 | Loader | Bias shape mismatch |
| E304 | Loader | NaN or infinity in weights or bias |
| E401 | IR / Optimizer | Internal IR inconsistency |
| E501 | Backend | Unsupported C backend operation |
| E601 | Verifier | C and NumPy outputs differ |
| E602 | Verifier | GCC not found or generated C failed to compile |
| W101 | Parser | Parser table has conflicts |
