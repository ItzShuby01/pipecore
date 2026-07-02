from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TokenizedLine:
    line_number: int
    label: str | None
    instruction_text: str | None


class Lexer:
    @staticmethod
    def tokenize(source_code: str) -> list[TokenizedLine]:
        tokenized_lines: list[TokenizedLine] = []

        for i, raw_line in enumerate(source_code.splitlines(), start=1):
            # Strip comments
            cleaned = raw_line.split(";", 1)[0].strip()
            if not cleaned:
                continue

            label: str | None = None
            instruction_text: str | None = None

            # Isolate labels
            if ":" in cleaned:
                label_part, remaining = cleaned.split(":", 1)
                label = label_part.strip()
                if not label.isidentifier():
                    raise SyntaxError(
                        f"Line {i}: Invalid label identifier name '{label}'")
                cleaned = remaining.strip()

            if cleaned:
                instruction_text = cleaned

            if label or instruction_text:
                tokenized_lines.append(
                    TokenizedLine(i, label, instruction_text))

        return tokenized_lines
