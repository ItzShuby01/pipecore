from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class ParsedOperand:
    text: str
    mode: int
    value: int | str


@dataclass
class ParsedInstruction:
    mnemonic: str
    operands: list[ParsedOperand]
    line_number: int


class Parser:
    @staticmethod
    def parse_integer(text: str) -> int:
        text = text.strip()
        if text.lower().startswith("0x"):
            return int(text, 16)
        return int(text)

    @classmethod
    def parse_operand(cls, op_text: str) -> ParsedOperand:
        op_text = op_text.strip()

        # Immediate Mode
        if op_text.startswith("#"):
            inner = op_text[1:]
            try:
                return ParsedOperand(op_text, 0, cls.parse_integer(inner))
            except ValueError:
                return ParsedOperand(op_text, 0, inner)

        # Registers and Ports
        reg_map = {"R0": 0, "R1": 1, "R2": 2, "R3": 3,
                   "IP": 4, "SP": 5, "IR": 6, "FLAGS": 7}
        port_map = {"P0": 0, "P1": 1, "P2": 2}
        upper_op = op_text.upper()

        if upper_op in reg_map:
            return ParsedOperand(op_text, 1, reg_map[upper_op])
        if upper_op in port_map:
            return ParsedOperand(op_text, 1, port_map[upper_op])

        # Memory Brackets
        if op_text.startswith("[") and op_text.endswith("]"):
            inner = op_text[1:-1].strip()

            # Indexed Mode [R1 + 4]
            if "+" in inner or "-" in inner:
                sign = "+" if "+" in inner else "-"
                parts = inner.split(sign)
                base_reg_str = parts[0].strip().upper()
                offset_str = parts[1].strip()

                if base_reg_str in reg_map:
                    base_code = reg_map[base_reg_str]
                    offset_val = cls.parse_integer(offset_str)
                    if sign == "-":
                        offset_val = -offset_val
                    packed_value = (base_code << 16) | (offset_val & 0xFFFF)
                    return ParsedOperand(op_text, 4, packed_value)

            # Register Indirect Mode [R2]
            if inner.upper() in reg_map:
                return ParsedOperand(op_text, 3, reg_map[inner.upper()])

            # Direct Memory Mode [1000]
            try:
                return ParsedOperand(op_text, 2, cls.parse_integer(inner))
            except ValueError:
                return ParsedOperand(op_text, 2, inner)

        return ParsedOperand(op_text, 0, op_text)

    @classmethod
    def parse_line(cls, inst_text: str, line_number: int) -> ParsedInstruction:
        tokens = re.split(r'\s+', inst_text, maxsplit=1)
        mnemonic = tokens[0]
        operands: list[ParsedOperand] = []

        if len(tokens) > 1:
            raw_ops = [o.strip() for o in tokens[1].split(",") if o.strip()]
            for rop in raw_ops:
                operands.append(cls.parse_operand(rop))

        return ParsedInstruction(mnemonic, operands, line_number)
