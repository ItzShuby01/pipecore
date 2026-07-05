from __future__ import annotations

import sys
from src.cpu.datapath import CPU
from src.assembler.translator import Translator
from src.loader.loader import Loader
from src.cpu.interrupt_controller import InterruptController
from src.cpu.pipeline import Pipeline


class Simulator:
    def __init__(self) -> None:
        self.cpu = CPU()
        self.translator = Translator()
        self.pipeline = Pipeline(self.cpu)
        self.cycle_count = 0

    def initialize_environment(self, main_source: str, isr_source: str) -> None:
        # IVT Setup
        self.cpu.memory.write(0x0000, 0x0050)

        main_bin = self.translator.assemble(main_source, start_address=0x0040)
        Loader.load(self.cpu, main_bin, start_address=0x0040)

        isr_bin = self.translator.assemble(isr_source, start_address=0x0050)
        Loader.load(self.cpu, isr_bin, start_address=0x0050)

    def run(self) -> None:
        is_silent = "silent" in sys.argv or "--silent" in sys.argv
        is_verbose = "verbose" in sys.argv or "--verbose" in sys.argv

        if not is_silent:
            print("\n--- PipeCore Pipeline Simulation ---")

        while self.cpu.running or not self.pipeline.is_empty():
            if not is_silent:
                print(f"\n[Clock Cycle {self.cycle_count}]")

            # Emulate external interrupt assertion on Cycle 1
            if self.cycle_count == 1:
                if not is_silent and not is_verbose:
                    print("[HARDWARE SIGNAL]: External Line INT0 pulled HIGH!")
                self.cpu.interrupt_asserted = 0

            if self.cpu.interrupt_asserted is not None:
                return_address = self.pipeline.get_interrupt_return_address()
                self.pipeline.flush()

                if not is_silent:
                    print(
                        f"[DEBUG INT]: Pushing context down for vector index {self.cpu.interrupt_asserted}")

                InterruptController.process_interrupts(
                    self.cpu, return_pc=return_address)

            self.pipeline.tick()
            self.cycle_count += 1

    def print_report(self) -> None:
        if hasattr(sys.stdout, 'silent_global_mute'):
            setattr(sys.stdout, 'silent_global_mute', False)

        print("\n========================================================")
        print("Registers Final State:")
        from src.common.enums import Register
        for reg in Register:
            val = self.cpu.registers[reg]
            print(f"  {reg.name:<5}: {val:<10} (0x{val:08X})")

        print(
            f"Main program execution state: {self.cpu.registers[Register.R1]}")
        print(f"ISR execution state: {self.cpu.registers[Register.R3]}")
        print(f"Total Simulation Clocks (Latency): {self.cycle_count} cycles")
        print("PipeCore simulation terminated successfully.")
