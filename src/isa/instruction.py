from __future__ import annotations
from dataclasses import dataclass, field
from src.common.enums import AddressingMode, Opcode


@dataclass
class Operand:
    mode: AddressingMode
    value: int


@dataclass
class Instruction:
    opcode: Opcode
    operand_count: int
    operands: list[Operand] = field(default_factory=list)
    flags: int = 0
