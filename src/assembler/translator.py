from __future__ import annotations
import struct
from src.assembler.lexer import Lexer
from src.assembler.parser import Parser, ParsedInstruction
from src.assembler.symbols import SymbolTable
from src.assembler.encoder import Encoder


class Translator:
    def __init__(self) -> None:
        self.symbols = SymbolTable()

    def assemble(self, source_code: str, start_address: int = 0x0040, bin_path: str | None = None, lst_path: str | None = None) -> list[int]:
        self.symbols = SymbolTable()
        tokenized_lines = Lexer.tokenize(source_code)

        current_address = start_address
        instructions_to_encode: list[tuple[int, ParsedInstruction]] = []

        #  Resolve Labels and Address Spans
        for token in tokenized_lines:
            if token.label:
                self.symbols.define(token.label, current_address)

            if token.instruction_text:
                p_inst = Parser.parse_line(
                    token.instruction_text, token.line_number)
                instructions_to_encode.append((current_address, p_inst))
                current_address += 4 * (1 + len(p_inst.operands))

        # Binary Object Emission
        binary_output: list[int] = []
        lst_lines = ["<address> - <HEXCODE> - <mnemonic>"]
        for addr, p_inst in instructions_to_encode:
            words, asm_str = Encoder.encode(p_inst, self.symbols)
            binary_output.extend(words)

            for idx, word in enumerate(words):
                loc = addr + (idx * 4)
                if idx == 0:
                    lst_lines.append(
                        f"{loc:04X}      - {word:08X}  - {asm_str}")
                else:
                    lst_lines.append(f"{loc:04X}      - {word:08X}")

        if bin_path:
            with open(bin_path, "wb") as f:
                for word in binary_output:
                    f.write(struct.pack(">I", word))

        if lst_path:
            with open(lst_path, "w") as f:
                f.write("\n".join(lst_lines) + "\n")

        return binary_output
