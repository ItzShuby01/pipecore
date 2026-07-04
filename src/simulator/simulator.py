from __future__ import annotations

from src.cpu.datapath import CPU
from src.assembler.translator import Translator
from src.loader.loader import Loader
from src.cpu.interrupt_controller import InterruptController
from src.cpu.pipeline import Pipeline
from src.common.enums import Register


class Simulator:
    def __init__(self) -> None:
        self.cpu = CPU()
        self.translator = Translator()
        self.pipeline = Pipeline(self.cpu)
        self.cycle_count = 0

    def initialize_environment(self, main_source: str, isr_source: str) -> None:
        # IVT
        self.cpu.memory.write(0x0000, 0x0050)

        main_bin = self.translator.assemble(main_source, start_address=0x0040)
        Loader.load(self.cpu, main_bin, start_address=0x0040)

        isr_bin = self.translator.assemble(isr_source, start_address=0x0050)
        Loader.load(self.cpu, isr_bin, start_address=0x0050)

    def run(self) -> None:
        print("\n--- PipeCore 5-Stage Pipelined Datapath Simulation ---")

        while self.cpu.running or not self.pipeline.is_empty():
            print(f"\n[Clock Cycle {self.cycle_count}]")

            if self.cycle_count == 1:
                print("[HARDWARE SIGNAL]: External Line INT0 pulled HIGH!")
                self.cpu.interrupt_asserted = 0

            if self.cpu.interrupt_asserted is not None:
                return_address = self.pipeline.get_interrupt_return_address()

                self.pipeline.flush()

                InterruptController.process_interrupts(
                    self.cpu, return_pc=return_address)

                print(
                    f"[DEBUG INT]: Pushing to Stack -> Intended Return IP: {return_address:#06x}, Saved FLAGS: {self.cpu.registers[Register.FLAGS]:#06x}, SP after push: {self.cpu.registers[Register.SP]:#06x}")

            self.pipeline.tick()
            self.cycle_count += 1

    def print_report(self) -> None:
        print("\n========================================================")
        print("Registers Final State:")
        from src.common.enums import Register
        for reg in Register:
            val = self.cpu.registers[reg]
            print(f"  {reg.name:<5}: {val:<10} (0x{val:08X})")

        print(
            f"Main program execution state: {self.cpu.registers[Register.R1]}")
        print(
            f"ISR execution state: {self.cpu.registers[Register.R3]}")
        print(f"Total Simulation Clocks (Latency): {self.cycle_count} cycles")
        print("PipeCore simulation terminated successfully.")
