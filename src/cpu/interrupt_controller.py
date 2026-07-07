from __future__ import annotations

import sys
from src.cpu.datapath import CPU
from src.common.enums import Register


class InterruptController:
    @staticmethod
    def process_interrupts(cpu: CPU, return_pc: int | None = None) -> None:
        """External interrupt handler loop stub"""
        if not cpu.running or cpu.interrupt_asserted is None:
            return
        intr_num = cpu.interrupt_asserted
        cpu.interrupt_asserted = None
        flags = cpu.read_register(int(Register.FLAGS))
        ip = return_pc if return_pc is not None else cpu.read_register(
            int(Register.IP))
        sp = cpu.read_register(int(Register.SP))
        sp = (sp - 1) & 0xFFFF
        cpu.memory.write(sp, ip)
        sp = (sp - 1) & 0xFFFF
        cpu.memory.write(sp, flags)
        cpu.write_register(int(Register.SP), sp)
        target_isr_address = cpu.memory.read(intr_num)
        cpu.write_register(int(Register.IP), target_isr_address)

    @staticmethod
    def process_trap(cpu: CPU, return_pc: int | None = None) -> None:
        """Processes Trap entry sequence."""
        if not cpu.running or not cpu.trap_request:
            return

        is_verbose = "verbose" in sys.argv or "--verbose" in sys.argv

        flags = cpu.read_register(int(Register.FLAGS))
        ip = return_pc if return_pc is not None else cpu.read_register(
            int(Register.IP))
        sp = cpu.read_register(int(Register.SP))

        if is_verbose:
            print("\nContext Save")
            print("------------")
            print("SP <- SP-1")
            print("MEM[SP] <- IP")

        sp = (sp - 1) & 0xFFFF
        cpu.memory.write(sp, ip)

        if is_verbose:
            print("SP <- SP-1")
            print("MEM[SP] <- FLAGS")

        sp = (sp - 1) & 0xFFFF
        cpu.memory.write(sp, flags)

        cpu.write_register(int(Register.SP), sp)

        if is_verbose:
            print("FLAGS.I <- 0")
        flags &= ~0x10
        cpu.write_register(int(Register.FLAGS), flags)

        target_isr_address = cpu.memory.read(0x0000)
        if is_verbose:
            print("IP <- MEM[IVT[0]]")
        cpu.write_register(int(Register.IP), target_isr_address)

        cpu.trap_request = False
