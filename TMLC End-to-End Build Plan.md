# TMLC: End-to-End Build Plan

Nov 20, 2026 · @hk

## Goal and definition of done

The project is finished when one trained 784 → 128 → 64 → 10 network goes from `mnist.tml` to `model.c`, and `python main.py verify examples/mnist.tml` prints PASS. Everything else (table display, memory report, extra tests) builds on that one path, so it gets built first and the rest is added around it.

Done means all of these hold:

- `python main.py build` writes `generated/model.c` and `model.h` with no `malloc`/`calloc` and only `static const` weights.
- `verify` reports a maximum absolute error and passes `np.allclose(atol=1e-5, rtol=1e-4)` on several input vectors.
- All 18 tests pass with `pytest`; the 14 invalid-input tests each fail with the expected error code and no `model.c` is written.
- Every command in the demo sequence runs from a clean clone using only the README.
- The report and slides contain real output from these runs, not placeholders.

## Repository layout

One package per compiler stage, one test file per stage, and everything the grader asks for (README, grammar, diagrams, examples, report, slides) lives in the same repo.

```text
tmlc/
├─ README.md                  setup, quick start, demo sequence, error-code table
├─ requirements.txt            numpy, pytest (plus torch or tensorflow only for training)
├─ main.py                    CLI: tokens | parse | tables | ast | semantic | ir | memory | build | verify
├─ tmlc/
│  ├─ errors.py               TmlcError(code, message, line, col); E/W code registry
│  ├─ lexer/
│  │  └─ lexer.py             Token, Lexer, keyword table, E001-E002
│  ├─ parser/
│  │  ├─ grammar.py           Production, Grammar, augmentation
│  │  ├─ first_follow.py      FIRST/FOLLOW, nullable
│  │  ├─ lr0.py               LR(0) items, closure, goto, SLR(1) table
│  │  ├─ lr1.py               CLR(1) items and table, LALR(1) by core merge
│  │  ├─ driver.py            shift/reduce loop, --trace output, E101
│  │  └─ tables_print.py      ACTION/GOTO printer, state and conflict counts
│  ├─ ast/
│  │  ├─ nodes.py             Model, InputDecl, OutputDecl, Dense, Activation
│  │  └─ builder.py           reduce actions that construct nodes; tree printer
│  ├─ semantic/
│  │  └─ analyzer.py          shape chain, dimension and path checks, E201-E2xx
│  ├─ loader/
│  │  └─ weights.py           numpy.load, shape/NaN/Inf checks, float32 cast, E301-E3xx
│  ├─ ir/
│  │  ├─ ops.py               INPUT, DENSE, RELU, SOFTMAX, DENSE_RELU, OUTPUT
│  │  └─ builder.py           AST + weights -> op list; IR printer
│  ├─ optimizer/
│  │  ├─ fuse.py              Dense + ReLU fusion
│  │  ├─ buffers.py           two-buffer allocation, memory report
│  │  └─ dce.py               dead-code elimination (last, optional)
│  ├─ backend/
│  │  ├─ c99.py               emits model.c and model.h
│  │  └─ templates.py         loop and softmax snippets
│  └─ verifier/
│     └─ verify.py            NumPy reference, gcc invocation, allclose, E601
├─ examples/
│  ├─ tiny.tml                Dense(4,8) -> ReLU -> Dense(8,2), the course example
│  ├─ mnist.tml               784-128-64-10
│  └─ weights/                tiny_*.npy, dense1_w.npy ... dense3_b.npy
├─ training/
│  ├─ train_mnist.py          trains the model, exports .npy in (in, out) orientation, prints accuracy
│  └─ make_tiny.py            seeded random weights for the 4-8-2 example
├─ tests/
│  ├─ fixtures/               18 small .tml files and corrupted .npy files
│  ├─ test_lexer.py  test_parser.py  test_semantic.py
│  ├─ test_loader.py test_codegen.py test_verifier.py
├─ generated/                  model.c, model.h (build output, committed once for the report)
├─ docs/
│  ├─ grammar.md              productions, token table, FIRST/FOLLOW, state and conflict counts
│  ├─ architecture.png        pipeline diagram (reuse the one from the slides)
│  ├─ examples/               saved outputs: tokens.txt, trace.txt, ast.txt, ir_opt.txt, memory.txt
│  ├─ screenshots/            one per command and one per error class
│  ├─ demo.mp4                2-3 minute screen recording
│  ├─ TMLC_report.docx / .pdf 8-12 pages
│  └─ TMLC_presentation.pptx  the 10-slide deck already built
└─ Makefile                   make test | make demo | make build
```

## Day-by-day build plan

Six build days plus one buffer day. Each day ends with a command that works and an output you save, so nothing is left to reconstruct for the report. Day 5 is the critical one: if it runs short, cut from days 4 and 6, never from day 5.

| Day | Build | Files produced | Exit check |
| --- | --- | --- | --- |
| 0 (2 h) | Repo skeleton, `errors.py` with the E/W code registry, argument parsing in `main.py`, git init, `requirements.txt` | `main.py`, `tmlc/errors.py`, `README.md` stub, `Makefile` | `python main.py --help` lists all 9 commands |
| 1 | Lexer: token classes, line/column tracking, comments, E001 and E002. Write `examples/tiny.tml` and `examples/mnist.tml` | `lexer/lexer.py`, `test_lexer.py`, both `.tml` files | `tokens examples/mnist.tml` prints the stream; tests 3 and 4 pass |
| 2 | Parser generator: grammar class, FIRST/FOLLOW, LR(0) closure and goto, SLR(1), CLR(1), LALR(1) by merging, driver with `--trace`. Then AST nodes built in the reduce actions | `parser/*.py`, `ast/*.py`, `test_parser.py`, `docs/grammar.md` | `parse --trace` shows every shift and reduce; `tables` prints state and conflict counts for all three; `ast` prints the tree; tests 5 and 6 pass |
| 3 | Semantic analyzer (shape chain, positive dims, declared input and output). Weight loader (existence, shapes, NaN/Inf, float32). Training script that exports `.npy` in (in, out) orientation | `semantic/analyzer.py`, `loader/weights.py`, `training/*.py`, `examples/weights/*.npy`, `test_semantic.py`, `test_loader.py` | `semantic` accepts both examples; tests 7-9, 11-16 pass; training script prints test accuracy |
| 4 | IR builder and printer. Dense+ReLU fusion. Two-buffer allocation and `memory` report. Dead-code elimination only if time allows | `ir/*.py`, `optimizer/*.py`, `docs/examples/ir_opt.txt`, `memory.txt` | `ir --opt` shows 8 ops before and 6 after; `memory` prints weight bytes and working-buffer bytes |
| 5 | C99 backend (static const weights, nested loops, stable softmax, `model_predict`). Verifier: NumPy reference, `gcc -std=c99`, `np.allclose`, E601. Run on `tiny.tml` first, then `mnist.tml` | `backend/*.py`, `verifier/verify.py`, `generated/model.c`, `model.h`, `test_codegen.py`, `test_verifier.py` | `verify examples/tiny.tml` then `verify examples/mnist.tml` print PASS with max abs error; tests 1, 2, 17, 18 pass |
| 6 | Run all 18 tests. Take screenshots, record the demo, measure inference time and `model.c` size. Update the report and slides with real numbers. Final clean-clone test of the README | `docs/screenshots/*`, `docs/demo.mp4`, `docs/TMLC_report.*`, updated `.pptx` | `make test` is green on a fresh clone; no placeholder text left in the report or deck |
| 7 (buffer) | Fix whatever slipped, rehearse the 10-minute talk, export slides to PDF as a backup | `TMLC_presentation.pdf` | Talk runs inside 10 minutes with the demo |

### Build order inside each stage

1. Tiny example first. Get `Dense(4,8) → ReLU → Dense(8,2)` through a stage before trying MNIST; a 4-8-2 mismatch is easy to read, a 784-128 one is not.
2. Write the failing test fixture before the check it exercises, so each error code has a test the moment it exists.
3. Save the output of every demo command to `docs/examples/` as soon as it works. Screenshots are taken last, from those same commands.

### Report and slides, in parallel

The report already has its structure, so each day's output drops into a known section: day 1 into 5.1, day 2 into 5.2–5.3 and Section 3.3, day 3 into 5.4–5.5, day 4 into 5.6–5.7, day 5 into 5.8–5.9 and Section 7. The existing 10-slide deck needs only its computed numbers (memory, status card) replaced with measured ones.

## Error codes and the 18 tests

Every diagnostic carries a code, a message and, where it applies, a line and column. The ranges are fixed by the report; the individual codes below extend its examples, so one code covers one failure and each test asserts a specific code, not just "an error".

| Code | Stage | Meaning |
| --- | --- | --- |
| E001 | Lexer | Invalid character |
| E002 | Lexer | Unterminated string |
| E101 | Parser | Unexpected token (includes unexpected end of input) |
| E201 | Semantic | Layer dimension mismatch, including first Dense vs input features |
| E202 | Semantic | Non-positive dimension |
| E203 | Semantic | Last Dense output differs from the output declaration |
| E204 | Semantic | Model has no Dense layer |
| E301 | Loader | Missing weight or bias file |
| E302 | Loader | Weight shape mismatch |
| E303 | Loader | Bias shape mismatch |
| E304 | Loader | NaN or infinity in weights or bias |
| E401 | IR / optimizer | Internal inconsistency (op shapes do not chain after a pass) |
| E501 | Backend | Unsupported C backend operation |
| E601 | Verifier | C and NumPy outputs differ |
| E602 | Verifier | gcc not found or generated C failed to compile |
| W101 | Parser | Table has conflicts (reported by `tables`, not fatal if the chosen table is conflict-free) |

### Test matrix

Each row is one pytest case with its own fixture under `tests/fixtures/`. Tests 3–16 must also assert that no `model.c` was written.

| # | Case | Fixture | Expected | File |
| --- | --- | --- | --- | --- |
| 1 | Valid MNIST 784→128→64→10 | `mnist.tml` | accepted, C generated | test\_codegen |
| 2 | Course example Dense(4,8)→ReLU→Dense(8,2) | `tiny.tml` | C matches NumPy | test\_verifier |
| 3 | Unknown character `@` | `bad_char.tml` | E001 with line:col | test\_lexer |
| 4 | Unterminated string | `open_string.tml` | E002 | test\_lexer |
| 5 | Missing semicolon | `no_semi.tml` | E101 | test\_parser |
| 6 | Extra tokens after closing brace | `trailing.tml` | E101 | test\_parser |
| 7 | Missing input declaration | `no_input.tml` | E101 (see decision 1) | test\_parser |
| 8 | Missing output declaration | `no_output.tml` | E101 (see decision 1) | test\_parser |
| 9 | Zero dimension, e.g. `Dense(0, 8, ...)` | `zero_dim.tml` | E202 (see decision 2) | test\_semantic |
| 10 | Unknown layer name, e.g. `Conv2D(...)` | `unknown_layer.tml` | E101 | test\_parser |
| 11 | Dense(784,128) then Dense(64,10) | `mismatch.tml` | E201 | test\_semantic |
| 12 | Last Dense output ≠ output declaration | `bad_output.tml` | E203 | test\_semantic |
| 13 | Missing `.npy` file | `missing_w.tml` | E301 | test\_loader |
| 14 | Wrong weight matrix shape | `bad_w_shape.npy` | E302 | test\_loader |
| 15 | Wrong bias shape | `bad_b_shape.npy` | E303 | test\_loader |
| 16 | Weights containing NaN | `nan_w.npy` | E304 | test\_loader |
| 17 | Softmax with very large logits (e.g. ±1000) | `big_logits.tml` | finite output, sums to 1 within 1e-5 | test\_codegen |
| 18 | Five different input vectors | `mnist.tml` | PASS on each | test\_verifier |

Tests 3–16 are the 14 invalid inputs; tests 1, 2, 17 and 18 are the valid or numerical ones, which matches the report's count.

## Evidence to capture

The report says it must not claim a result that was not produced, so every number and screenshot below comes from a real run. Save the text output first (`> docs/examples/<name>.txt`), then screenshot the same command.

| Evidence | Command | Save as | Goes into |
| --- | --- | --- | --- |
| Token stream | `python main.py tokens examples/mnist.tml` | `tokens.txt`, `01_tokens.png` | Report 5.1, slide 4 |
| Parser trace | `python main.py parse examples/mnist.tml --trace` | `trace.txt`, `02_trace.png` | Report 5.2, slide 5 |
| LR tables, state count, conflicts per table type | `python main.py tables` | `tables.txt`, `03_tables.png` | Report 3.3 (the "to fill in" line), slide 5 |
| AST | `python main.py ast examples/mnist.tml` | `ast.txt`, `04_ast.png` | Report 5.3, slide 6 |
| Semantic accept and E201 reject | `python main.py semantic` on `mnist.tml` and `mismatch.tml` | `05_semantic_ok.png`, `05_semantic_E201.png` | Report 5.4, slide 6 |
| Original and optimized IR | `python main.py ir examples/mnist.tml --opt` | `ir_opt.txt`, `06_ir.png` | Report 5.6–5.7, slide 7 |
| Memory report | `python main.py memory examples/mnist.tml` | `memory.txt` | Report 5.7, slide 8 (replaces the computed 437,544 B and 768 B) |
| Generated C | `python main.py build examples/mnist.tml` | `model_head.txt` (first 40 lines of `model.c`, all of `model.h`) | Report 5.8, slide 8 code panel |
| Numerical comparison | `python main.py verify examples/mnist.tml` | `verify.txt`, `07_verify.png` | Report 7, slide 9 |
| One invalid input per error class | tests 3, 5, 9, 11, 13, 14, 16 | `err_E001.png` ... `err_E304.png` | Report 7.2 |
| Corrupted-weight demo (the strongest validation) | corrupt one `.npy` shape, run `build`, then `ls generated/` | `08_corrupt_weight.png` | Report 6, demo |

### Numbers the report and slides are still waiting for

- Training accuracy of the exported MNIST model (printed by `train_mnist.py`)
- Maximum absolute error between C and NumPy, over all five test vectors
- Size of `model.c` in KB (`wc -c generated/model.c`)
- Measured inference time of `model_predict` (average over 10,000 calls with `clock_gettime`, built with `-O2`)
- LR(0) state count and the number of conflicts in SLR(1), CLR(1) and LALR(1)
- Actual `memory` output, to replace the figures computed from the architecture

Once these exist, update slide 8's tiles, the status card on slide 10, and the closing paragraph in report 9.2. Ask me to regenerate the deck with the real values and I will rebuild it from the same script.

## Deliverables checklist

The course brief lists seven deliverables; two are already drafted (the slide deck and the architecture diagram), and the rest are produced by the plan above.

- [ ] **Source code with README and setup instructions.** README covers Python and GCC versions, `pip install -r requirements.txt`, the training step, the demo sequence and the error-code table. Done on day 0, finished on day 6.
- [ ] **Grammar specification and architecture diagram.** `docs/grammar.md` (productions, token table, FIRST/FOLLOW, state and conflict counts) is day 2. The architecture diagram exists as `02_compiler_pipeline.png`; copy it to `docs/architecture.png`.
- [ ] **AST, IR and generated-target examples.** The saved outputs in `docs/examples/` and `generated/model.c` and `model.h` (days 2, 4, 5).
- [ ] **At least 15 test cases including invalid inputs.** 18 planned, 14 invalid; green `pytest` run saved as `docs/examples/pytest.txt` (days 1–5, confirmed day 6).
- [ ] **Screenshots or a short demo recording.** Screenshots per the evidence table, plus a 2–3 minute `demo.mp4` following the course checklist: compile a valid example, show AST and IR, run the generated code, trigger an invalid-input diagnostic (day 6).
- [ ] **8–12 page report.** The existing report text is the skeleton; the three "to fill in" lines and the Section 7 evidence table get real content (day 6). Export to PDF and check the page count.
- [ ] **8–10 slide team presentation.** The 10-slide deck is built; swap in measured numbers and add a screenshot or two from the real run (day 6).
- [ ] **Explicit limitations and future extensions.** Already in report Section 8 and on slide 10; check they still match what was actually built.

The brief's own summary of the deliverable is "input source + tokens/AST + generated target + execution evidence". Each of the four has a named file above.

## Decisions, risks and cuts

Four decisions are worth making before day 1, two of them because the report's test plan does not match its own grammar; the rest are risks with a prepared answer.

### Decisions to make now

1. **Missing input or output declaration (tests 7 and 8).** The grammar makes `InputDecl OutputDecl` mandatory in `ModelBody`, so a missing one is a syntax error (E101), not a semantic one. Recommended: keep the grammar strict, which keeps the LR tables small and likely conflict-free, and move tests 7 and 8 to the parser. Then the semantic stage owns tests 9, 11 and 12, and the report's stage column plus the slide 10 chart change (Semantic 5 → 3, Parser 2 → 4). The alternative, optional declarations in the grammar, makes the semantic check reachable but adds grammar complexity for no new capability.
2. **"Negative dimension" (test 9).** The lexer has no minus sign, so `-8` is an invalid character (E001), and only a zero dimension reaches the semantic check (E202). Recommended: test zero for E202 and, if you want negative covered too, add it as a lexer case under E001.
3. **Training data.** The report names MNIST. If the machine can download it (torchvision or Keras), use it. If not, `sklearn.datasets.load_digits` is a no-download fallback, but it is 8×8 = 64 inputs, so `mnist.tml` becomes 64 → 32 → 10 and the report and slide numbers change. Decide before day 3.
4. **Unreachable semantic rules.** "Every Dense layer has a weight and bias path" is already guaranteed by the grammar (two STRING tokens are required). Keep the check as a cheap safety net, but do not count it as a tested rule.

### Risks

| Risk | Why it matters | Answer |
| --- | --- | --- |
| CLR(1) table is large or slow to build | CLR(1) item sets are the biggest part of the generator | Test the generator on a toy expression grammar first; the model grammar is small, so state counts stay in the dozens |
| Grammar has conflicts in one table type | The report says it is not assumed conflict-free | Report the conflict count as a result; the driver uses whichever table is conflict-free (LALR(1) first) |
| C and NumPy differ by more than 1e-5 | Float32 summation order can differ across 784-term dot products | Compute the NumPy reference in float32 with the same loop order for the check, and write floats into C with `%.9g` so they round-trip exactly; if still tight, compare pre-softmax logits first to locate the gap |
| Huge `model.c` | 109,386 float literals is several MB of source | Fine for GCC; mention it under limitations (already there) and note the file size as a measured result |
| Weight paths break when run from another folder | Paths resolve relative to the `.tml` folder, not the working directory | Resolve with `Path(tml_file).parent / path` and add one test that runs from a different working directory |
| GCC missing on the demo machine | Verification depends on it | `verify` reports E602 with a clear message; test the demo on the machine you will present from |
| Day 5 overruns | Backend and verifier are the only stages with no fallback | Build the tiny example end to end first; MNIST is then a data change, not a code change |

### If time runs short, cut in this order

1. Dead-code elimination (the report already calls it low priority).
2. The demo video, replaced by the screenshots in the evidence table.
3. LALR(1) merging, keeping SLR(1) and CLR(1) tables only (update the report text to match).
4. Per-layer detail in the memory report.

Never cut: the lexer, a working parser with a table, the semantic shape check, weight validation, the C backend, the NumPy verifier, and the 15 required tests.

## Microcontroller compatibility and extension

No board is available yet, so on-device demonstration is a planned extension, not part of the first delivery. The generated C is designed so that it can move to a microcontroller later without changes to the compiler.

### Why the output is already compatible

- Plain C99, no `malloc` or `calloc`, no operating system calls, no file I/O.
- Weights are `static const float`, which a microcontroller toolchain places in flash instead of RAM.
- Working memory is two static buffers (768 B for the MNIST model), so RAM use is known at compile time.
- One entry point, `void model_predict(const float input[784], float output[10]);`, with no other dependency than `<math.h>` for `expf` in Softmax.

### What fits where

| Target class | Flash | Fits |
| --- | --- | --- |
| Arduino Uno / Nano (AVR) | 32 KB | The 4-8-2 example only |
| Raspberry Pi Pico (RP2040) | 2 MB | Both models |
| ESP32 | typically 4 MB | Both models |
| STM32F4-class | 512 KB – 1 MB | Both models; MNIST needs at least 512 KB of flash |

The MNIST weights are about 437 KB, so the board needs at least 512 KB of flash; the Uno and Nano can only run the 4-8-2 example. This is the one hardware limit to state in the report.

### Extension plan for when a board is available

1. Add `firmware/main.c` (or an `.ino`) that calls `model_predict` on a fixed input and prints the outputs over serial.
2. Add `make firmware`, which builds the same generated `model.c` for the target instead of rewriting the model.
3. Copy the fixed input and the expected output from `verify` into the firmware, and check that the board prints the same numbers as NumPy.
4. Record the flash and RAM size report and the serial output as evidence.

If a simulator such as Wokwi or QEMU becomes an option before a board does, steps 1–3 can run there first.

### What to say in the report and slides until then

Section 8.2 (future extensions) gets one line: "Run the generated C on a microcontroller or simulator and compare its output with NumPy." The report should describe the output as designed for microcontroller use, not as tested on one, so nothing claims a result that was not produced.
