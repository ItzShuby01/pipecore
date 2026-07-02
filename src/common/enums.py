from enum import IntEnum, unique


@unique
class Opcode(IntEnum):
    NOP = 0x00
    HALT = 0x01
    MOV = 0x10
    LOAD = 0x11
    STORE = 0x12
    PUSH = 0x13
    POP = 0x14
    ADD = 0x20
    SUB = 0x21
    MUL = 0x22
    DIV = 0x23
    MOD = 0x24
    INC = 0x25
    DEC = 0x26
    CMP = 0x30
    JMP = 0x31
    JZ = 0x32
    JNZ = 0x33
    JLT = 0x34
    JGT = 0x35
    CALL = 0x40
    RET = 0x41
    IRET = 0x42
    IN = 0x50
    OUT = 0x51


@unique
class AddressingMode(IntEnum):
    IMMEDIATE = 0x0
    REGISTER = 0x1
    DIRECT_MEMORY = 0x2
    REGISTER_INDIRECT = 0x3
    INDEXED = 0x4


@unique
class Register(IntEnum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    IP = 4
    SP = 5
    IR = 6
    FLAGS = 7


class IOPort(IntEnum):
    P0 = 0x0
    P1 = 0x1
    P2 = 0x2
