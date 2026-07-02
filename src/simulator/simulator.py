from __future__ import annotations

from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register
from src.assembler.translator import Translator
from src.loader.loader import Loader
from src.cpu.interrupt_controller import InterruptController


class Simulator:
    def __init__(self) -> None:
        self.cpu = CPU()
        self.translator = Translator()
        self.cycle_count = 0

    def initialize_environment(self, main_source: str, isr_source: str) -> None:
        self.cpu.memory.write(0x0000, 0x0050)

        main_bin = self.translator.assemble(main_source, start_address=0x0040)
        Loader.load(self.cpu, main_bin, start_address=0x0040)

        isr_bin = self.translator.assemble(isr_source, start_address=0x0050)
        Loader.load(self.cpu, isr_bin, start_address=0x0050)

    def run(self) -> None:
        while self.cpu.running:
            if self.cycle_count == 1:
                print("[HARDWARE SIGNAL]: Line INT0 pulled HIGH!")
                self.cpu.interrupt_asserted = 0

            InterruptController.process_interrupts(self.cpu)

            if not self.cpu.running:
                break

            word = self.cpu.fetch()
            instruction = decode(word, self.cpu)
            execute(self.cpu, instruction)
            self.cycle_count += 1

    def print_report(self) -> None:
        print("\nRegisters Final State:")
        for reg in Register:
            val = self.cpu.registers[reg]
            print(f"  {reg.name:<5}: {val:<10} (0x{val:08X})")

        print("\n--- Test Interrupt Verification ---")
        print(
            f"Main program execution state: {self.cpu.registers[Register.R1]}")
        print(
            f"ISR execution state: {self.cpu.registers[Register.R3]}")
        print("PipeCore halted successfully")
