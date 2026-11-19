"""Error types and diagnostics registry for TMLC."""

from __future__ import annotations

from typing import Final

# Diagnostic code definitions
ERROR_CODES: Final[dict[str, str]] = {
    "E001": "Invalid character",
    "E002": "Unterminated string",
    "E101": "Unexpected token",
    "E201": "Layer dimension mismatch",
    "E202": "Non-positive dimension",
    "E203": "Output dimension mismatch",
    "E204": "Model has no Dense layer",
    "E301": "Missing weight or bias file",
    "E302": "Weight shape mismatch",
    "E303": "Bias shape mismatch",
    "E304": "NaN or infinity in weights or bias",
    "E401": "IR internal inconsistency",
    "E501": "Unsupported C backend operation",
    "E601": "C and NumPy outputs differ",
    "E602": "gcc not found or generated C failed to compile",
    "W101": "Parser table has conflicts",
}


class TmlcError(Exception):
    """Base exception for all TMLC compiler errors.

    Attributes:
        code: The error code string (e.g. 'E001').
        message: Detailed diagnostic message.
        line: 1-based source line number, if applicable.
        col: 1-based source column number, if applicable.
    """

    def __init__(
        self,
        code: str,
        message: str,
        line: int | None = None,
        col: int | None = None,
    ) -> None:
        self.code: str = code
        self.message: str = message
        self.line: int | None = line
        self.col: int | None = col

        desc = ERROR_CODES.get(code, "Unknown error")
        location = ""
        if line is not None and col is not None:
            location = f" at line {line}, col {col}"
        elif line is not None:
            location = f" at line {line}"

        full_msg = f"[{code}] {desc}{location}: {message}"
        super().__init__(full_msg)

    def __str__(self) -> str:
        """Format error as human-readable diagnostic string."""
        desc = ERROR_CODES.get(self.code, "Unknown error")
        location = ""
        if self.line is not None and self.col is not None:
            location = f" at line {self.line}, col {self.col}"
        elif self.line is not None:
            location = f" at line {self.line}"
        return f"[{self.code}] {desc}{location}: {self.message}"
