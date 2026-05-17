from __future__ import annotations

from src.cpu.datapath import CPU
from src.common.enums import Opcode, AddressingMode
from src.isa.instruction import Instruction


def execute(cpu: CPU, instruction: Instruction) -> None:
    if instruction.opcode == Opcode.HALT:
        cpu.running = False
    elif instruction.opcode == Opcode.MOV:
        execute_mov(cpu, instruction)
    elif instruction.opcode == Opcode.NOP:
        pass
    else:
        raise NotImplementedError(
            f"Opcode {instruction.opcode} not implemented")


def execute_mov(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 2:
        raise ValueError(
            "MOV requires at least source and destination operand")

    src = instruction.operands[0]
    dst = instruction.operands[1]

    if src.mode == AddressingMode.IMMEDIATE:
        value = src.value
    elif src.mode == AddressingMode.REGISTER:
        value = cpu.read_register(src.value)
    else:
        raise NotImplementedError(f"Unsupported MOV source mode: {src.mode}")

    if dst.mode == AddressingMode.REGISTER:
        cpu.write_register(dst.value, value)
    else:
        raise NotImplementedError(
            f"Unsupported MOV destination mode: {dst.mode}")
