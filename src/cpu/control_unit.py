from __future__ import annotations

from src.cpu.datapath import CPU
from src.common.enums import Opcode, AddressingMode, IOPort
from src.isa.instruction import Instruction


def execute(cpu: CPU, instruction: Instruction) -> None:
    if instruction.opcode == Opcode.HALT:
        cpu.running = False
    elif instruction.opcode == Opcode.MOV:
        execute_mov(cpu, instruction)
    elif instruction.opcode == Opcode.OUT:
        execute_out(cpu, instruction)
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


def execute_out(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 2:
        raise ValueError("OUT requires a port operand and a source operand")

    port_operand = instruction.operands[0]
    src_operand = instruction.operands[1]

    port_id = IOPort(port_operand.value)

    if src_operand.mode == AddressingMode.REGISTER:
        data_value = cpu.read_register(src_operand.value)
    else:
        raise NotImplementedError(
            "OUT only supports reading from a register source right now")

    char = chr(data_value & 0xFF)

    if port_id in cpu.output_ports:
        cpu.output_ports[port_id].append(char)
    else:
        cpu.output_ports[port_id] = [char]
