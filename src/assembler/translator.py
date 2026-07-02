from __future__ import annotations
from src.assembler.lexer import Lexer
from src.assembler.parser import Parser, ParsedInstruction
from src.assembler.symbols import SymbolTable
from src.assembler.encoder import Encoder


class Translator:
    def __init__(self) -> None:
        self.symbols = SymbolTable()

    def assemble(self, source_code: str, start_address: int = 0x0040) -> list[int]:
        self.symbols = SymbolTable()
        tokenized_lines = Lexer.tokenize(source_code)

        current_address = start_address
        instructions_to_encode: list[ParsedInstruction] = []

        #  Resolve Labels and Address Spans
        for token in tokenized_lines:
            if token.label:
                self.symbols.define(token.label, current_address)

            if token.instruction_text:
                p_inst = Parser.parse_line(
                    token.instruction_text, token.line_number)
                instructions_to_encode.append(p_inst)
                current_address += 1 + len(p_inst.operands)

        # Binary Object Emission
        binary_output: list[int] = []
        for p_inst in instructions_to_encode:
            binary_output.extend(Encoder.encode(p_inst, self.symbols))

        return binary_output
