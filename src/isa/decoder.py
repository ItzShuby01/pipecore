from __future__ import annotations

from src.common.enums import Opcode, AddressingMode, Register
from src.isa.instruction import Instruction, Operand
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cpu.datapath import CPU


def decode(word: int, cpu: CPU, base_pc: int | None = None) -> Instruction:
    opcode = Opcode((word >> 24) & 0xFF)
    operand_count = (word >> 20) & 0xF

    modes = [
        AddressingMode((word >> 16) & 0xF),
        AddressingMode((word >> 12) & 0xF),
        AddressingMode((word >> 8) & 0xF),
    ]

    flags = word & 0xFF

    if base_pc is None:
        base_pc = cpu.read_register(int(Register.IP)) - 4

    operands: list[Operand] = []
    for i in range(operand_count):
        operand_word = cpu.memory.read(base_pc + 4 + (i * 4))
        operands.append(Operand(mode=modes[i], value=operand_word))

    return Instruction(
        opcode=opcode,
        operand_count=operand_count,
        operands=operands,
        flags=flags,
    )
