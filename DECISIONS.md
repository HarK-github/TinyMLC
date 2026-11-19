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
