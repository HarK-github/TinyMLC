"""TMLC CLI entry point."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

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
        print(f"Parsing {args.file} (trace={args.trace}) - stage will be implemented in Day 2")
        return 0

    if args.command == "tables":
        print("Displaying LR tables - stage will be implemented in Day 2")
        return 0

    if args.command == "ast":
        print(f"Generating AST for {args.file} - stage will be implemented in Day 2")
        return 0

    if args.command == "semantic":
        print(f"Running semantic analysis on {args.file} - stage will be implemented in Day 3")
        return 0

    if args.command == "ir":
        print(f"Generating IR for {args.file} (opt={args.opt}) - stage will be implemented in Day 4")
        return 0

    if args.command == "memory":
        print(f"Memory report for {args.file} - stage will be implemented in Day 4")
        return 0

    if args.command == "build":
        print(f"Building {args.file} into {args.out_dir} - stage will be implemented in Day 5")
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
