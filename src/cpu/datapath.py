from __future__ import annotations

from src.memory.memory import Memory
from src.common.enums import Register, IOPort


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

        self.output_ports: dict[IOPort, list[str]] = {
            IOPort.P1: []
        }

        self.interrupt_asserted: int | None = None

    def fetch(self) -> int:
        instruction = self.memory.read(self.registers[Register.IP])
        self.registers[Register.IR] = instruction
        self.registers[Register.IP] += 1
        return instruction

    def read_register(self, reg_id: int) -> int:
        return self.registers[Register(reg_id)]

    def write_register(self, reg_id: int, value: int) -> None:
        self.registers[Register(reg_id)] = value & 0xFFFFFFFF
