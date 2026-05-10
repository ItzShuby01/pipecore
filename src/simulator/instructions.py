from __future__ import annotations

from src.simulator.cpu import CPU
from src.common.enums import Opcode


def execute(cpu: CPU, opcode: int) -> None:
    if opcode == Opcode.HALT:  # HALT
        cpu.running = False
    elif opcode == Opcode.NOP:
        pass
    else:
        raise NotImplementedError(f"Opcode {opcode:#x} not implemented")
