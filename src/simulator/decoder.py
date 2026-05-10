from __future__ import annotations

from src.common.enums import Opcode


# bits 31–24 = opcode -> shift right by 24 isolates opcode
def decode_opcode(word: int) -> Opcode:
    return Opcode((word >> 24) & 0xFF)
