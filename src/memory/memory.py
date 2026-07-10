from __future__ import annotations


class Memory:
    # PipeCore memory map 0x0000–0xFFFF = 65536 addresses
    def __init__(self, size: int = 65536) -> None:
        self._data: list[int] = [0] * size

    def read(self, address: int) -> int:
        b0 = self._data[address]
        b1 = self._data[(address + 1) % len(self._data)]
        b2 = self._data[(address + 2) % len(self._data)]
        b3 = self._data[(address + 3) % len(self._data)]
        return (b0 << 24) | (b1 << 16) | (b2 << 8) | b3

    def write(self, address: int, value: int) -> None:
        value &= 0xFFFFFFFF  # force PipeCore 32-bit range
        self._data[address] = (value >> 24) & 0xFF
        self._data[(address + 1) % len(self._data)] = (value >> 16) & 0xFF
        self._data[(address + 2) % len(self._data)] = (value >> 8) & 0xFF
        self._data[(address + 3) % len(self._data)] = value & 0xFF
