"""TMLC CLI entry point."""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections.abc import Sequence

from tmlc.errors import TmlcError


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser for TMLC."""
    parser = argparse.ArgumentParser(
        prog="tmlc",
        description="TMLC: TinyML Model-to-C Compiler",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available compiler stages and tools",
        required=True,
    )

    # 1. tokens
    tokens_parser = subparsers.add_parser(
        "tokens",
        help="Tokenize a .tml source file and print the token stream",
    )
    tokens_parser.add_argument("file", help="Path to .tml model file")

    # 2. parse
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse a .tml model file with optional shift/reduce trace",
    )
    parse_parser.add_argument("file", help="Path to .tml model file")
    parse_parser.add_argument(
        "--trace",
        action="store_true",
        help="Print shift/reduce driver execution trace",
    )

    # 3. tables
    subparsers.add_parser(
        "tables",
        help="Display LR parser tables, state counts, and conflict reports",
    )

    # 4. ast
    ast_parser = subparsers.add_parser(
        "ast",
        help="Parse .tml file and print the Abstract Syntax Tree (AST)",
    )
    ast_parser.add_argument("file", help="Path to .tml model file")

    # 5. semantic
    semantic_parser = subparsers.add_parser(
        "semantic",
        help="Run semantic checks on model declarations, shapes, and weights",
    )
    semantic_parser.add_argument("file", help="Path to .tml model file")

    # 6. ir
    ir_parser = subparsers.add_parser(
        "ir",
        help="Build and print Intermediate Representation (IR)",
    )
    ir_parser.add_argument("file", help="Path to .tml model file")
    ir_parser.add_argument(
        "--opt",
        action="store_true",
        help="Apply IR optimizations (Dense+ReLU fusion)",
    )

    # 7. memory
    memory_parser = subparsers.add_parser(
        "memory",
        help="Generate static memory footprint and buffer allocation report",
    )
    memory_parser.add_argument("file", help="Path to .tml model file")

    # 8. build
    build_parser = subparsers.add_parser(
        "build",
        help="Compile .tml model and generate standalone C99 model.c and model.h",
    )
    build_parser.add_argument("file", help="Path to .tml model file")
    build_parser.add_argument(
        "--out-dir",
        default="generated",
        help="Output directory for generated C files (default: generated)",
    )

    # 9. verify
    verify_parser = subparsers.add_parser(
        "verify",
        help="Compile generated C with GCC and verify against NumPy reference",
    )
    verify_parser.add_argument("file", help="Path to .tml model file")

    return parser


def dispatch_command(args: argparse.Namespace) -> int:
    """Dispatch the parsed CLI command to the appropriate compiler subsystem."""
    if args.command == "tokens":
        from tmlc.lexer.lexer import Lexer

        lexer = Lexer.from_file(args.file)
        tokens = lexer.tokenize()
        for token in tokens:
            print(token)
        return 0

    if args.command == "parse":
        from tmlc.parser.driver import ParserDriver

        driver = ParserDriver()
        if args.trace:
            driver.parse_file(args.file, trace_callback=print)
        else:
            driver.parse_file(args.file)
        print(f"Successfully parsed {args.file}")
        return 0

    if args.command == "tables":
        from tmlc.parser.grammar import get_tmlc_grammar
        from tmlc.parser.lr0 import build_slr1_table
        from tmlc.parser.tables_print import format_slr1_table

        grammar = get_tmlc_grammar()
        table = build_slr1_table(grammar)
        print(format_slr1_table(table))
        return 0

    if args.command == "ast":
        from tmlc.ast.nodes import format_ast
        from tmlc.parser.driver import ParserDriver

        driver = ParserDriver()
        ast = driver.parse_file(args.file)
        print(format_ast(ast))
        return 0

    if args.command == "semantic":
        from tmlc.loader.weights import WeightLoader
        from tmlc.parser.driver import ParserDriver
        from tmlc.semantic.analyzer import SemanticAnalyzer

        driver = ParserDriver()
        ast = driver.parse_file(args.file)

        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        base_dir = pathlib.Path(args.file).parent
        loader = WeightLoader()
        loaded_weights = loader.load_weights(ast, base_dir)

        print(
            f"Semantic and weight checks passed for {args.file}: "
            f"Model '{ast.name}' (in={ast.input_decl.dim}, out={ast.output_decl.dim}, "
            f"{len(loaded_weights)} Dense layers verified)"
        )
        return 0

    if args.command == "ir":
        from tmlc.ir.builder import build_ir
        from tmlc.loader.weights import WeightLoader
        from tmlc.optimizer.fuse import fuse_dense_relu
        from tmlc.parser.driver import ParserDriver
        from tmlc.semantic.analyzer import SemanticAnalyzer

        driver = ParserDriver()
        ast = driver.parse_file(args.file)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        base_dir = pathlib.Path(args.file).parent
        loader = WeightLoader()
        weights = loader.load_weights(ast, base_dir)

        ir_prog = build_ir(ast, weights)
        if args.opt:
            ir_opt = fuse_dense_relu(ir_prog)
            print(f"; Unoptimized IR : {len(ir_prog.ops)} ops")
            print(f"; Optimized IR   : {len(ir_opt.ops)} ops (Dense+ReLU fused)")
            print(ir_opt.format())
        else:
            print(ir_prog.format())
        return 0

    if args.command == "memory":
        from tmlc.ir.builder import build_ir
        from tmlc.loader.weights import WeightLoader
        from tmlc.optimizer.buffers import allocate_buffers
        from tmlc.optimizer.fuse import fuse_dense_relu
        from tmlc.parser.driver import ParserDriver
        from tmlc.semantic.analyzer import SemanticAnalyzer

        driver = ParserDriver()
        ast = driver.parse_file(args.file)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        base_dir = pathlib.Path(args.file).parent
        loader = WeightLoader()
        weights = loader.load_weights(ast, base_dir)

        ir_prog = build_ir(ast, weights)
        ir_opt = fuse_dense_relu(ir_prog)
        _, report = allocate_buffers(ir_opt)
        print(report.format())
        return 0

    if args.command == "build":
        print(
            f"Building {args.file} into {args.out_dir} - stage will be implemented in Day 5"
        )
        return 0

    if args.command == "verify":
        print(f"Verifying {args.file} - stage will be implemented in Day 5")
        return 0

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI main entry point with global error handling."""
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        return dispatch_command(args)
    except TmlcError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
