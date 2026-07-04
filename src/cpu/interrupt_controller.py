from __future__ import annotations
from src.cpu.datapath import CPU
from src.common.enums import Register


class InterruptController:
    @staticmethod
    def process_interrupts(cpu: CPU, return_pc: int | None = None) -> None:
        """Checks if a hardware interrupt line is pulled high and handles the execution switch."""
        if not cpu.running or cpu.interrupt_asserted is None:
            return

        intr_num = cpu.interrupt_asserted
        cpu.interrupt_asserted = None

        flags = cpu.read_register(int(Register.FLAGS))

        ip = return_pc if return_pc is not None else cpu.read_register(
            int(Register.IP))
        sp = cpu.read_register(int(Register.SP))

        # SP =  IP first -> then FLAGS
        sp = (sp - 1) & 0xFFFF
        cpu.memory.write(sp, ip)

        sp = (sp - 1) & 0xFFFF
        cpu.memory.write(sp, flags)

        cpu.write_register(int(Register.SP), sp)

        target_isr_address = cpu.memory.read(intr_num)
        cpu.write_register(int(Register.IP), target_isr_address)
        print(
            f"[CPU HARDWARE]: Diverting execution to ISR at 0x{target_isr_address:04X}")
