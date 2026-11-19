# TMLC Formal Grammar Specification

This document provides the formal grammar specification for the TinyML Model-to-C Compiler (TMLC), including context-free productions, lexical token definitions, FIRST/FOLLOW sets, and SLR(1) parsing automaton statistics.

---

## 1. Context-Free Grammar Productions

The grammar uses an augmented start symbol `Start` for LR parsing.

```bnf
0:  Start           -> Model
1:  Model           -> MODEL IDENT LBRACE ModelBody RBRACE
2:  ModelBody       -> InputDecl OutputDecl LayerList
3:  InputDecl       -> INPUT COLON INT SEMICOLON
4:  OutputDecl      -> OUTPUT COLON INT SEMICOLON
5:  LayerList       -> LayerList Layer
6:  LayerList       -> Layer
7:  Layer           -> DenseLayer
8:  Layer           -> ActivationLayer
9:  DenseLayer      -> DENSE LPAREN INT COMMA INT COMMA STRING COMMA STRING RPAREN SEMICOLON
10: ActivationLayer -> RELU SEMICOLON
11: ActivationLayer -> SOFTMAX SEMICOLON
```

---

## 2. Lexical Token Table

| Token Name | Lexical Pattern / Keyword | Description |
| --- | --- | --- |
| `MODEL` | `model` | Model declaration keyword |
| `INPUT` | `input` | Input dimension declaration keyword |
| `OUTPUT` | `output` | Output dimension declaration keyword |
| `DENSE` | `Dense` | Fully connected layer keyword |
| `RELU` | `ReLU` | Rectified Linear Unit activation |
| `SOFTMAX` | `Softmax` | Normalized exponential activation |
| `IDENT` | `[A-Za-z_][A-Za-z0-9_]*` | Identifier (model name) |
| `INT` | `[0-9]+` | Unsigned decimal integer literal |
| `STRING` | `"([^"\n\r\\]|\\.)*"` | Double-quoted string literal |
| `LBRACE` | `{` | Left curly brace |
| `RBRACE` | `}` | Right curly brace |
| `LPAREN` | `(` | Left parenthesis |
| `RPAREN` | `)` | Right parenthesis |
| `COLON` | `:` | Colon delimiter |
| `SEMICOLON` | `;` | Statement terminator |
| `COMMA` | `,` | Argument separator |
| `EOF` | End-of-file | End of input stream |

---

## 3. FIRST and FOLLOW Sets

### FIRST Sets
- `FIRST(Start)` = `{ 'MODEL' }`
- `FIRST(Model)` = `{ 'MODEL' }`
- `FIRST(ModelBody)` = `{ 'INPUT' }`
- `FIRST(InputDecl)` = `{ 'INPUT' }`
- `FIRST(OutputDecl)` = `{ 'OUTPUT' }`
- `FIRST(LayerList)` = `{ 'DENSE', 'RELU', 'SOFTMAX' }`
- `FIRST(Layer)` = `{ 'DENSE', 'RELU', 'SOFTMAX' }`
- `FIRST(DenseLayer)` = `{ 'DENSE' }`
- `FIRST(ActivationLayer)` = `{ 'RELU', 'SOFTMAX' }`

### FOLLOW Sets
- `FOLLOW(Start)` = `{ 'EOF' }`
- `FOLLOW(Model)` = `{ 'EOF' }`
- `FOLLOW(ModelBody)` = `{ 'RBRACE' }`
- `FOLLOW(InputDecl)` = `{ 'OUTPUT' }`
- `FOLLOW(OutputDecl)` = `{ 'DENSE', 'RELU', 'SOFTMAX' }`
- `FOLLOW(LayerList)` = `{ 'DENSE', 'RELU', 'SOFTMAX', 'RBRACE' }`
- `FOLLOW(Layer)` = `{ 'DENSE', 'RELU', 'SOFTMAX', 'RBRACE' }`
- `FOLLOW(DenseLayer)` = `{ 'DENSE', 'RELU', 'SOFTMAX', 'RBRACE' }`
- `FOLLOW(ActivationLayer)` = `{ 'DENSE', 'RELU', 'SOFTMAX', 'RBRACE' }`

---

## 4. SLR(1) Automaton Statistics

- **Total LR(0) States**: 37
- **Terminals**: 17
- **Nonterminals**: 9
- **Productions**: 12
- **Shift/Reduce Conflicts**: 0
- **Reduce/Reduce Conflicts**: 0
- **SLR(1) Status**: Fully conflict-free deterministic SLR(1) grammar.
