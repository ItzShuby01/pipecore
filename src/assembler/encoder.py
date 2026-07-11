from __future__ import annotations
from src.common.enums import Opcode, AddressingMode, Register, IOPort
from src.assembler.parser import ParsedInstruction
from src.assembler.symbols import SymbolTable


class Encoder:
    @staticmethod
    def encode(p_inst: ParsedInstruction, symbols: SymbolTable) -> tuple[list[int], str]:
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

        operand_list = []
        opcode = Opcode((header_word >> 24) & 0xFF)
        operand_count = (header_word >> 20) & 0xF

        modes = [
            (header_word >> 16) & 0xF,
            (header_word >> 12) & 0xF,
            (header_word >> 8) & 0xF,
        ]

        for i in range(operand_count):
            word_val = machine_words[i + 1]
            mode = modes[i]

            if mode == AddressingMode.IMMEDIATE:
                operand_list.append(f"#0x{word_val:04X}")
            elif mode == AddressingMode.REGISTER:
                if (opcode == Opcode.IN or opcode == Opcode.OUT) and i == 0:
                    try:
                        operand_list.append(IOPort(word_val).name)
                    except ValueError:
                        operand_list.append(f"P{word_val}")
                else:
                    try:
                        operand_list.append(Register(word_val).name)
                    except ValueError:
                        operand_list.append(f"R{word_val}")
            elif mode == AddressingMode.DIRECT_MEMORY:
                operand_list.append(f"[0x{word_val:04X}]")
            elif mode == AddressingMode.REGISTER_INDIRECT:
                try:
                    reg_name = Register(word_val).name
                except ValueError:
                    reg_name = f"R{word_val}"
                operand_list.append(f"[{reg_name}]")
            elif mode == AddressingMode.INDEXED:
                reg_code = (word_val >> 16) & 0xFFFF
                offset_val = word_val & 0xFFFF
                if offset_val & 0x8000:
                    offset_val -= 0x10000
                try:
                    reg_name = Register(reg_code).name
                except ValueError:
                    reg_name = f"R{reg_code}"
                sign = "+" if offset_val >= 0 else "-"
                operand_list.append(f"[{reg_name} {sign} {abs(offset_val)}]")
            else:
                operand_list.append(str(word_val))

        asm_str = opcode.name
        if operand_list:
            asm_str += " " + ", ".join(operand_list)

        return machine_words, asm_str
