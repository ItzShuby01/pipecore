from __future__ import annotations
from src.cpu.datapath import CPU


class Loader:
    @staticmethod
    def load(cpu: CPU, binary: list[int], start_address: int) -> None:
        """Injects compiled binary streams into the system memory map."""
        for offset, word in enumerate(binary):
            cpu.memory.write(start_address + offset * 4, word)
