from __future__ import annotations

from src.common.enums import Opcode, AddressingMode
from src.isa.instruction import Instruction, Operand
from typing import TYPE_CHECKING

# bits 31–24 = opcode -> shift right by 24 isolates opcode

if TYPE_CHECKING:
    from src.cpu.datapath import CPU


def decode(word: int, cpu: CPU) -> Instruction:
    opcode = Opcode((word >> 24) & 0xFF)
    operand_count = (word >> 20) & 0xF

    modes = [
        AddressingMode((word >> 16) & 0xF),
        AddressingMode((word >> 12) & 0xF),
        AddressingMode((word >> 8) & 0xF),
    ]

    flags = word & 0xFF

    # Pull trailing words based on operand_count
    operands: list[Operand] = []
    for i in range(operand_count):
        operand_word = cpu.fetch()
        operands.append(Operand(mode=modes[i], value=operand_word))

    return Instruction(
        opcode=opcode,
        operand_count=operand_count,
        operands=operands,
        flags=flags,
    )
