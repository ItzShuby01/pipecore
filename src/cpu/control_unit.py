from __future__ import annotations

from src.cpu.datapath import CPU
from src.common.enums import Opcode, AddressingMode, IOPort, Register
from src.isa.instruction import Instruction, Operand
import sys


def read_operand(cpu: CPU, operand: Operand) -> int:
    """Resolves any of the 5 addressing modes to read a 32-bit value."""
    mode = operand.mode
    val = operand.value

    if mode == AddressingMode.IMMEDIATE:
        return val
    elif mode == AddressingMode.REGISTER:
        return cpu.read_register(val)
    elif mode.name == "DIRECT_MEMORY" or mode.value == 2:
        return cpu.memory.read(val)
    elif mode.name == "REGISTER_INDIRECT" or mode.value == 3:
        addr = cpu.read_register(val)
        return cpu.memory.read(addr)
    elif mode.name == "INDEXED" or mode.value == 4:
        base_reg = (val >> 16) & 0xFFFF
        offset = val & 0xFFFF
        if offset & 0x8000:
            offset -= 0x10000
        addr = (cpu.read_register(base_reg) + offset) & 0xFFFF
        return cpu.memory.read(addr)
    else:
        raise NotImplementedError(f"Unsupported read addressing mode: {mode}")


def write_operand(cpu: CPU, operand: Operand, value: int) -> None:
    """Resolves addressing modes to write 32-bit value to a destination."""
    mode = operand.mode
    val = operand.value
    value &= 0xFFFFFFFF

    if mode == AddressingMode.REGISTER:
        cpu.write_register(val, value)
    elif mode.name == "DIRECT_MEMORY" or mode.value == 2:
        cpu.memory.write(val, value)
    elif mode.name == "REGISTER_INDIRECT" or mode.value == 3:
        addr = cpu.read_register(val)
        cpu.memory.write(addr, value)
    elif mode.name == "INDEXED" or mode.value == 4:
        base_reg = (val >> 16) & 0xFFFF
        offset = val & 0xFFFF
        if offset & 0x8000:
            offset -= 0x10000
        addr = (cpu.read_register(base_reg) + offset) & 0xFFFF
        cpu.memory.write(addr, value)
    else:
        raise NotImplementedError(f"Unsupported write addressing mode: {mode}")


def update_flags(cpu: CPU, result: int, overflow: bool = False) -> None:
    """Helper to update Z, N, and O flags"""
    flags = 0
    if (result & 0xFFFFFFFF) == 0:
        flags |= (1 << 0)
    if result & 0x80000000:
        flags |= (1 << 1)
    if overflow:
        flags |= (1 << 3)
    cpu.write_register(int(Register.FLAGS), flags)


def execute(cpu: CPU, instruction: Instruction) -> None:
    if instruction.opcode == Opcode.HALT:
        cpu.running = False
    elif instruction.opcode == Opcode.NOP:
        pass
    elif instruction.opcode == Opcode.MOV:
        execute_mov(cpu, instruction)
    elif instruction.opcode == Opcode.LOAD:
        execute_load(cpu, instruction)
    elif instruction.opcode == Opcode.STORE:
        execute_store(cpu, instruction)
    elif instruction.opcode == Opcode.PUSH:
        execute_push(cpu, instruction)
    elif instruction.opcode == Opcode.POP:
        execute_pop(cpu, instruction)
    elif instruction.opcode == Opcode.ADD:
        execute_add(cpu, instruction)
    elif instruction.opcode == Opcode.SUB:
        execute_sub(cpu, instruction)
    elif instruction.opcode == Opcode.MUL:
        execute_mul(cpu, instruction)
    elif instruction.opcode == Opcode.DIV:
        execute_div(cpu, instruction)
    elif instruction.opcode == Opcode.MOD:
        execute_mod(cpu, instruction)
    elif instruction.opcode == Opcode.INC:
        execute_inc(cpu, instruction)
    elif instruction.opcode == Opcode.DEC:
        execute_dec(cpu, instruction)
    elif instruction.opcode == Opcode.CMP:
        execute_cmp(cpu, instruction)
    elif instruction.opcode == Opcode.JMP:
        execute_jmp(cpu, instruction)
    elif instruction.opcode == Opcode.JZ:
        execute_jz(cpu, instruction)
    elif instruction.opcode == Opcode.JNZ:
        execute_jnz(cpu, instruction)
    elif instruction.opcode in (Opcode.JLT, getattr(Opcode, 'JLT', None)):
        execute_jlt(cpu, instruction)
    elif instruction.opcode == Opcode.JGT:
        execute_jgt(cpu, instruction)
    elif instruction.opcode == Opcode.CALL:
        execute_call(cpu, instruction)
    elif instruction.opcode == Opcode.RET:
        execute_ret(cpu, instruction)
    elif instruction.opcode == Opcode.IRET:
        execute_iret(cpu, instruction)
    elif instruction.opcode == Opcode.IN:
        execute_in(cpu, instruction)
    elif instruction.opcode == Opcode.OUT:
        execute_out(cpu, instruction)
    else:
        raise NotImplementedError(
            f"Opcode {instruction.opcode} not implemented")


def execute_mov(cpu: CPU, instruction: Instruction) -> None:
    val = read_operand(cpu, instruction.operands[0])
    write_operand(cpu, instruction.operands[1], val)


def execute_load(cpu: CPU, instruction: Instruction) -> None:
    val = read_operand(cpu, instruction.operands[0])
    write_operand(cpu, instruction.operands[1], val)


def execute_store(cpu: CPU, instruction: Instruction) -> None:
    val = read_operand(cpu, instruction.operands[0])
    write_operand(cpu, instruction.operands[1], val)


def execute_push(cpu: CPU, instruction: Instruction) -> None:
    value = read_operand(cpu, instruction.operands[0])
    current_sp = cpu.read_register(int(Register.SP))
    new_sp = (current_sp - 1) & 0xFFFF
    cpu.write_register(int(Register.SP), new_sp)
    cpu.memory.write(new_sp, value)


def execute_pop(cpu: CPU, instruction: Instruction) -> None:
    current_sp = cpu.read_register(int(Register.SP))
    if current_sp == 0xFFFF:
        raise IndexError("Stack Underflow Error!")
    value = cpu.memory.read(current_sp)
    write_operand(cpu, instruction.operands[0], value)
    cpu.write_register(int(Register.SP), (current_sp + 1) & 0xFFFF)


def execute_add(cpu: CPU, instruction: Instruction) -> None:
    val1 = read_operand(cpu, instruction.operands[0])
    val2 = read_operand(cpu, instruction.operands[1])
    result = (val1 + val2) & 0xFFFFFFFF
    update_flags(cpu, result)
    write_operand(cpu, instruction.operands[2], result)


def execute_sub(cpu: CPU, instruction: Instruction) -> None:
    val1 = read_operand(cpu, instruction.operands[0])
    val2 = read_operand(cpu, instruction.operands[1])
    result = (val1 - val2) & 0xFFFFFFFF
    update_flags(cpu, result)
    write_operand(cpu, instruction.operands[2], result)


def execute_mul(cpu: CPU, instruction: Instruction) -> None:
    val1 = read_operand(cpu, instruction.operands[0])
    val2 = read_operand(cpu, instruction.operands[1])
    result = (val1 * val2) & 0xFFFFFFFF
    update_flags(cpu, result)
    write_operand(cpu, instruction.operands[2], result)


def execute_div(cpu: CPU, instruction: Instruction) -> None:
    val1 = read_operand(cpu, instruction.operands[0])
    val2 = read_operand(cpu, instruction.operands[1])
    result = (val1 // val2) if val2 != 0 else 0
    update_flags(cpu, result)
    write_operand(cpu, instruction.operands[2], result)


def execute_mod(cpu: CPU, instruction: Instruction) -> None:
    val1 = read_operand(cpu, instruction.operands[0])
    val2 = read_operand(cpu, instruction.operands[1])
    result = (val1 % val2) if val2 != 0 else 0
    update_flags(cpu, result)
    write_operand(cpu, instruction.operands[2], result)


def execute_inc(cpu: CPU, instruction: Instruction) -> None:
    val = read_operand(cpu, instruction.operands[0])
    result = (val + 1) & 0xFFFFFFFF
    update_flags(cpu, result)
    write_operand(cpu, instruction.operands[0], result)


def execute_dec(cpu: CPU, instruction: Instruction) -> None:
    val = read_operand(cpu, instruction.operands[0])
    result = (val - 1) & 0xFFFFFFFF
    update_flags(cpu, result)
    write_operand(cpu, instruction.operands[0], result)


def execute_cmp(cpu: CPU, instruction: Instruction) -> None:
    val1 = read_operand(cpu, instruction.operands[0])
    val2 = read_operand(cpu, instruction.operands[1])
    result = (val1 - val2) & 0xFFFFFFFF
    update_flags(cpu, result)


def execute_jmp(cpu: CPU, instruction: Instruction) -> None:
    target = read_operand(cpu, instruction.operands[0])
    cpu.write_register(int(Register.IP), target)


def execute_jz(cpu: CPU, instruction: Instruction) -> None:
    flags = cpu.read_register(int(Register.FLAGS))
    if flags & (1 << 0):
        target = read_operand(cpu, instruction.operands[0])
        cpu.write_register(int(Register.IP), target)


def execute_jnz(cpu: CPU, instruction: Instruction) -> None:
    flags = cpu.read_register(int(Register.FLAGS))
    if not (flags & (1 << 0)):
        target = read_operand(cpu, instruction.operands[0])
        cpu.write_register(int(Register.IP), target)


def execute_jlt(cpu: CPU, instruction: Instruction) -> None:
    flags = cpu.read_register(int(Register.FLAGS))
    n = bool(flags & (1 << 1))
    v = bool(flags & (1 << 3))
    if n != v:
        target = read_operand(cpu, instruction.operands[0])
        cpu.write_register(int(Register.IP), target)


def execute_jgt(cpu: CPU, instruction: Instruction) -> None:
    flags = cpu.read_register(int(Register.FLAGS))
    z = bool(flags & (1 << 0))
    n = bool(flags & (1 << 1))
    v = bool(flags & (1 << 3))
    if not z and (n == v):
        target = read_operand(cpu, instruction.operands[0])
        cpu.write_register(int(Register.IP), target)


def execute_call(cpu: CPU, instruction: Instruction) -> None:
    target_address = read_operand(cpu, instruction.operands[0])
    return_address = cpu.read_register(int(Register.IP))
    current_sp = cpu.read_register(int(Register.SP))
    new_sp = (current_sp - 1) & 0xFFFF
    cpu.write_register(int(Register.SP), new_sp)
    cpu.memory.write(new_sp, return_address)
    cpu.write_register(int(Register.IP), target_address)


def execute_ret(cpu: CPU, instruction: Instruction) -> None:
    current_sp = cpu.read_register(int(Register.SP))
    if current_sp == 0xFFFF:
        raise IndexError("Stack Underflow Error: RET called on empty stack!")
    return_address = cpu.memory.read(current_sp)
    cpu.write_register(int(Register.SP), (current_sp + 1) & 0xFFFF)
    cpu.write_register(int(Register.IP), return_address)


def execute_iret(cpu: CPU, instruction: Instruction) -> None:
    """Pops state in strict inverse order of trap generation."""
    current_sp = cpu.read_register(int(Register.SP))
    is_verbose = "verbose" in sys.argv or "--verbose" in sys.argv

    if is_verbose:
        print("\nOn return:")
        print("IRET")

    # Top of stack contains FLAGS
    saved_flags = cpu.memory.read(current_sp)
    current_sp = (current_sp + 1) & 0xFFFF
    cpu.write_register(int(Register.FLAGS), saved_flags)
    if is_verbose:
        print("Restore FLAGS")

    # Next item down is return execution address
    return_address = cpu.memory.read(current_sp)
    current_sp = (current_sp + 1) & 0xFFFF
    cpu.write_register(int(Register.IP), return_address)
    if is_verbose:
        print("Restore IP")
        print("Resume Program")

    cpu.write_register(int(Register.SP), current_sp)


def execute_in(cpu: CPU, instruction: Instruction) -> None:
    port_operand = instruction.operands[0]
    port_id = IOPort(port_operand.value)
    is_verbose = "verbose" in sys.argv or "--verbose" in sys.argv

    if port_id == IOPort.P0:
        input_value = cpu.io_ports[IOPort.P0]
        write_operand(cpu, instruction.operands[1], input_value)

        cpu.io_ports[IOPort.P2] &= ~1

        if is_verbose:
            print("\nInside the ISR:")
            print(f"IN P0,R{instruction.operands[1].value}")
            print(f"P0 -> R{instruction.operands[1].value}")
            print("P2.INPUT_READY <- 0")

    elif port_id == IOPort.P2:
        status_value = cpu.io_ports[IOPort.P2]
        write_operand(cpu, instruction.operands[1], status_value)
    else:
        raise ValueError(
            f"Architectural Error: Port {port_id.name} is write-only/invalid for IN.")


def execute_out(cpu: CPU, instruction: Instruction) -> None:
    port_operand = instruction.operands[0]
    src_operand = instruction.operands[1]
    port_id = IOPort(port_operand.value)

    data_value = read_operand(cpu, src_operand)
    char = chr(data_value & 0xFF)

    if port_id == IOPort.P1:
        cpu.output_ports[IOPort.P1].append(char)
    else:
        raise ValueError(
            f"Architectural Error: Port {port_id.name} is not configured as output.")
