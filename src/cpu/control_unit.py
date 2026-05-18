from __future__ import annotations

from src.cpu.datapath import CPU
from src.common.enums import Opcode, AddressingMode, IOPort, Register
from src.isa.instruction import Instruction


def execute(cpu: CPU, instruction: Instruction) -> None:
    if instruction.opcode == Opcode.HALT:
        cpu.running = False
    elif instruction.opcode == Opcode.MOV:
        execute_mov(cpu, instruction)
    elif instruction.opcode == Opcode.OUT:
        execute_out(cpu, instruction)
    elif instruction.opcode == Opcode.ADD:
        execute_add(cpu, instruction)
    elif instruction.opcode == Opcode.CMP:
        execute_cmp(cpu, instruction)
    elif instruction.opcode == Opcode.JNZ:
        execute_jnz(cpu, instruction)
    elif instruction.opcode == Opcode.JMP:
        execute_jmp(cpu, instruction)
    elif instruction.opcode == Opcode.NOP:
        pass
    elif instruction.opcode == Opcode.PUSH:
        execute_push(cpu, instruction)
    elif instruction.opcode == Opcode.POP:
        execute_pop(cpu, instruction)
    else:
        raise NotImplementedError(
            f"Opcode {instruction.opcode} not implemented")


def execute_mov(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 2:
        raise ValueError(
            "MOV requires at least source and destination operands")

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
        raise ValueError("OUT requires port and source operands")

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


def execute_add(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 3:
        raise ValueError("ADD requires three operands: src1, src2, dst")

    src1, src2, dst = instruction.operands[0], instruction.operands[1], instruction.operands[2]

    val1 = src1.value if src1.mode == AddressingMode.IMMEDIATE else cpu.read_register(
        src1.value)
    val2 = src2.value if src2.mode == AddressingMode.IMMEDIATE else cpu.read_register(
        src2.value)

    result = (val1 + val2) & 0xFFFFFFFF

    if dst.mode == AddressingMode.REGISTER:
        cpu.write_register(dst.value, result)
    else:
        raise NotImplementedError("ADD destination must be a register")

    flags = 0
    if result == 0:
        flags |= (1 << 0)  # Set Z

    if result & 0x80000000:
        flags |= (1 << 1)  # Set N

    cpu.write_register(int(Register.FLAGS), flags)


def execute_cmp(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 2:
        raise ValueError("CMP requires two operands")

    src1, src2 = instruction.operands[0], instruction.operands[1]
    val1 = src1.value if src1.mode == AddressingMode.IMMEDIATE else cpu.read_register(
        src1.value)
    val2 = src2.value if src2.mode == AddressingMode.IMMEDIATE else cpu.read_register(
        src2.value)

    result = (val1 - val2) & 0xFFFFFFFF

    flags = 0
    if result == 0:
        flags |= (1 << 0)  # Set Z
    if result & 0x80000000:
        flags |= (1 << 1)  # Set N

    cpu.write_register(int(Register.FLAGS), flags)


def execute_jnz(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 1:
        raise ValueError("JNZ requires target address")
    target_operand = instruction.operands[0]
    target_address = target_operand.value if target_operand.mode == AddressingMode.IMMEDIATE else cpu.read_register(
        target_operand.value)
    flags = cpu.read_register(int(Register.FLAGS))
    z_flag = flags & (1 << 0)

    if not z_flag:
        cpu.write_register(int(Register.IP), target_address)


def execute_jmp(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 1:
        raise ValueError("JMP requires target address")
    target_operand = instruction.operands[0]
    target_address = target_operand.value if target_operand.mode == AddressingMode.IMMEDIATE else cpu.read_register(
        target_operand.value)
    cpu.write_register(int(Register.IP), target_address)


def execute_push(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 1:
        raise ValueError("PUSH requires a source operand")
    src = instruction.operands[0]
    value = src.value if src.mode == AddressingMode.IMMEDIATE else cpu.read_register(
        src.value)
    current_sp = cpu.read_register(int(Register.SP))
    new_sp = (current_sp - 1) & 0xFFFF  # --SP
    cpu.write_register(int(Register.SP), new_sp)

    cpu.memory.write(new_sp, value)


def execute_pop(cpu: CPU, instruction: Instruction) -> None:
    if len(instruction.operands) < 1:
        raise ValueError("POP requires destination register operand")
    dst = instruction.operands[0]
    if dst.mode != AddressingMode.REGISTER:
        raise NotImplementedError("POP destination must be register")
    current_sp = cpu.read_register(int(Register.SP))
    if current_sp == 0xFFFF:
        raise IndexError("Stack Underflow Error !")
    value = cpu.memory.read(current_sp)
    cpu.write_register(dst.value, value)

    new_sp = (current_sp + 1) & 0xFFFF  # SP++
    cpu.write_register(int(Register.SP), new_sp)
