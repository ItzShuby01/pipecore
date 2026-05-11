from __future__ import annotations


class Memory:
    # PipeCore memory map 0x0000–0xFFFF = 65536 addresses
    def __init__(self, size: int = 65536) -> None:
        self._data: list[int] = [0] * size

    def read(self, address: int) -> int:
        return self._data[address]

    def write(self, address: int, value: int) -> None:
        self._data[address] = value & 0xFFFFFFFF  # force PipeCore 32-bit range
