"""Hand-written lexer for TMLC language."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Final

from tmlc.errors import TmlcError

KEYWORDS: Final[dict[str, str]] = {
    "model": "MODEL",
    "input": "INPUT",
    "output": "OUTPUT",
    "Dense": "DENSE",
    "ReLU": "RELU",
    "Softmax": "SOFTMAX",
}

SINGLE_CHAR_TOKENS: Final[dict[str, str]] = {
    "{": "LBRACE",
    "}": "RBRACE",
    "(": "LPAREN",
    ")": "RPAREN",
    ":": "COLON",
    ";": "SEMICOLON",
    ",": "COMMA",
}


@dataclass(frozen=True)
class Token:
    """Represents a lexical token.

    Attributes:
        type: The token type name (e.g. 'MODEL', 'IDENT', 'INT').
        value: The token value (string or integer).
        line: 1-based source line where the token starts.
        col: 1-based source column where the token starts.
    """

    type: str
    value: str | int
    line: int
    col: int

    def __str__(self) -> str:
        """Format token for debug output and trace."""
        return f"{self.type}({self.value!r}) at {self.line}:{self.col}"


class Lexer:
    """Hand-written lexical analyzer for .tml source code."""

    def __init__(self, source: str) -> None:
        self.source: str = source
        self.pos: int = 0
        self.line: int = 1
        self.col: int = 1

    @classmethod
    def from_file(cls, path: str | pathlib.Path) -> Lexer:
        """Construct a Lexer from a file path."""
        p = pathlib.Path(path)
        content = p.read_text(encoding="utf-8")
        return cls(content)

    def _peek(self, offset: int = 0) -> str:
        """Return character at pos + offset without consuming it, or empty string on EOF."""
        target = self.pos + offset
        if target < len(self.source):
            return self.source[target]
        return ""

    def _advance(self) -> str:
        """Consume and return the current character, updating line and column numbers."""
        if self.pos >= len(self.source):
            return ""

        char = self.source[self.pos]
        self.pos += 1

        if char == "\r":
            # Check for CRLF
            if self.pos < len(self.source) and self.source[self.pos] == "\n":
                self.pos += 1
            self.line += 1
            self.col = 1
            return "\n"
        elif char == "\n":
            self.line += 1
            self.col = 1
            return "\n"
        else:
            self.col += 1
            return char

    def _skip_whitespace_and_comments(self) -> None:
        """Skip whitespace and single/multi-line comments."""
        while self.pos < len(self.source):
            char = self._peek()

            # Whitespace
            if char in " \t\r\n":
                self._advance()
                continue

            # Single-line comment: //
            if char == "/" and self._peek(1) == "/":
                while self.pos < len(self.source) and self._peek() not in "\r\n":
                    self._advance()
                continue

            # Single-line comment: #
            if char == "#":
                while self.pos < len(self.source) and self._peek() not in "\r\n":
                    self._advance()
                continue

            # Block comment: /* ... */
            if char == "/" and self._peek(1) == "*":
                start_line = self.line
                start_col = self.col
                self._advance()  # /
                self._advance()  # *
                closed = False
                while self.pos < len(self.source):
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance()  # *
                        self._advance()  # /
                        closed = True
                        break
                    self._advance()
                if not closed:
                    raise TmlcError(
                        "E001", "Unterminated block comment", start_line, start_col
                    )
                continue

            break

    def _read_string(self) -> Token:
        """Scan a string literal enclosed in double quotes."""
        start_line = self.line
        start_col = self.col
        self._advance()  # consume opening quote

        chars: list[str] = []
        while True:
            if self.pos >= len(self.source):
                raise TmlcError(
                    "E002", "Unterminated string literal", start_line, start_col
                )

            char = self._peek()
            if char in "\r\n":
                raise TmlcError(
                    "E002", "Unterminated string literal", start_line, start_col
                )

            if char == "\\":
                self._advance()
                if self.pos >= len(self.source):
                    raise TmlcError(
                        "E002", "Unterminated string literal", start_line, start_col
                    )
                escaped = self._advance()
                if escaped == "n":
                    chars.append("\n")
                elif escaped == "t":
                    chars.append("\t")
                elif escaped == "\\":
                    chars.append("\\")
                elif escaped == '"':
                    chars.append('"')
                else:
                    chars.append(escaped)
                continue

            if char == '"':
                self._advance()  # consume closing quote
                break

            chars.append(self._advance())

        return Token("STRING", "".join(chars), start_line, start_col)

    def _read_number(self) -> Token:
        """Scan an unsigned integer literal."""
        start_line = self.line
        start_col = self.col
        digits: list[str] = []

        while self._peek().isdigit():
            digits.append(self._advance())

        val_str = "".join(digits)
        return Token("INT", int(val_str), start_line, start_col)

    def _read_identifier_or_keyword(self) -> Token:
        """Scan an identifier or keyword."""
        start_line = self.line
        start_col = self.col
        chars: list[str] = []

        while self._peek().isalnum() or self._peek() == "_":
            chars.append(self._advance())

        text = "".join(chars)
        token_type = KEYWORDS.get(text, "IDENT")
        return Token(token_type, text, start_line, start_col)

    def next_token(self) -> Token:
        """Scan and return the next token from the source."""
        self._skip_whitespace_and_comments()

        if self.pos >= len(self.source):
            return Token("EOF", "", self.line, self.col)

        char = self._peek()
        start_line = self.line
        start_col = self.col

        # String literal
        if char == '"':
            return self._read_string()

        # Number literal
        if char.isdigit():
            return self._read_number()

        # Keyword or Identifier
        if char.isalpha() or char == "_":
            return self._read_identifier_or_keyword()

        # Single character delimiters
        if char in SINGLE_CHAR_TOKENS:
            token_type = SINGLE_CHAR_TOKENS[char]
            self._advance()
            return Token(token_type, char, start_line, start_col)

        # Invalid character (e.g. '@', '-', etc.)
        self._advance()
        raise TmlcError("E001", f"Invalid character '{char}'", start_line, start_col)

    def tokenize(self) -> list[Token]:
        """Scan entire source into a list of tokens ending with EOF."""
        tokens: list[Token] = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type == "EOF":
                break
        return tokens
