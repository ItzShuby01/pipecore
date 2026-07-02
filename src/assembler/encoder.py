from __future__ import annotations
from src.common.enums import Opcode
from src.assembler.parser import ParsedInstruction
from src.assembler.symbols import SymbolTable


class Encoder:
    @staticmethod
    def encode(p_inst: ParsedInstruction, symbols: SymbolTable) -> list[int]:
        try:
            opcode_enum = Opcode[p_inst.mnemonic.upper()]
        except KeyError:
            raise SyntaxError(
                f"Line {p_inst.line_number}: Unknown opcode mnemonic '{p_inst.mnemonic}'")

        opcode_val = opcode_enum.value
        op_count = len(p_inst.operands)

        mode1 = p_inst.operands[0].mode if op_count > 0 else 0
        mode2 = p_inst.operands[1].mode if op_count > 1 else 0
        mode3 = p_inst.operands[2].mode if op_count > 2 else 0

        header_word = (
            (opcode_val << 24) |
            (op_count << 20) |
            (mode1 << 16) |
            (mode2 << 12) |
            (mode3 << 8)
        ) & 0xFFFFFFFF

        machine_words = [header_word]

        for op in p_inst.operands:
            if isinstance(op.value, str):
                resolved_val = symbols.resolve(op.value)
                machine_words.append(resolved_val & 0xFFFFFFFF)
            else:
                machine_words.append(op.value & 0xFFFFFFFF)

        return machine_words
