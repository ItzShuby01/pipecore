from __future__ import annotations

from src.memory.memory import Memory
from src.common.enums import Register


class CPU:
    def __init__(self) -> None:
        self.memory = Memory()

        self.registers: dict[Register, int] = {
            Register.R0: 0,
            Register.R1: 0,
            Register.R2: 0,
            Register.R3: 0,
            Register.IP: 0x0040,  # program execution starts at 0x40
            Register.SP: 0xFFFF,  # stack grows downward
            Register.IR: 0,
            Register.FLAGS: 0,
        }

        self.running = True

    def fetch(self) -> int:
        instruction = self.memory.read(self.registers[Register.IP])
        self.registers[Register.IR] = instruction
        self.registers[Register.IP] += 1
        return instruction
