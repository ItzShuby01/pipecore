from __future__ import annotations

import sys
from src.cpu.datapath import CPU
from src.assembler.translator import Translator
from src.loader.loader import Loader
from src.cpu.interrupt_controller import InterruptController
from src.cpu.pipeline import Pipeline
from src.common.enums import IOPort, Register


class Simulator:
    def __init__(self) -> None:
        self.cpu = CPU()
        self.translator = Translator()
        self.pipeline = Pipeline(self.cpu)
        self.cycle_count = 0
        self.input_schedule: list[tuple[int, str]] = []
        self.next_input_id = 1
        self.current_resumed_id: int | None = None
        self.current_resumed_token: str | None = None

    def initialize_environment(self, main_source: str, isr_source: str, input_schedule: list[tuple[int, str]] | None = None) -> None:
        self.cpu.memory.write(0x0000, 0x0050)

        main_bin = self.translator.assemble(main_source, start_address=0x0040)
        Loader.load(self.cpu, main_bin, start_address=0x0040)

        isr_bin = self.translator.assemble(isr_source, start_address=0x0050)
        Loader.load(self.cpu, isr_bin, start_address=0x0050)

        if input_schedule is not None:
            self.input_schedule = input_schedule

    def run(self) -> None:
        is_silent = "silent" in sys.argv or "--silent" in sys.argv
        is_verbose = "verbose" in sys.argv or "--verbose" in sys.argv

        if not is_silent:
            print("\n--- PipeCore Pipeline Simulation ---")

        max_cycles = 30
        deferred_inputs: list[tuple[str, int]] = []

        while (self.cpu.running or not self.pipeline.is_empty()) and self.cycle_count < max_cycles:
            if not is_silent:
                print(f"\n[Tick {self.cycle_count}]")

            p0_busy = (self.cpu.io_ports[IOPort.P2] & 1) != 0
            if not p0_busy and deferred_inputs:
                token, input_id = deferred_inputs.pop(0)
                self.cpu.io_ports[IOPort.P0] = ord(token)
                self.cpu.io_ports[IOPort.P2] |= 1
                self.cpu.trap_request = True
                self.current_resumed_id = input_id
                self.current_resumed_token = token

                if is_verbose:
                    header = f"Pending Input #{input_id} Ready"
                    print(f"\n{header}")
                    print("-" * len(header))
                    print("P2.INPUT_READY <- 1")
                    print("\nWaiting for Interrupt Enable...")

            for tick, token in self.input_schedule:
                if tick == self.cycle_count:
                    flags = self.cpu.read_register(int(Register.FLAGS))
                    interrupts_enabled = (flags & 0x10) != 0
                    p0_busy = (self.cpu.io_ports[IOPort.P2] & 1) != 0

                    if p0_busy or not interrupts_enabled:
                        input_id = self.next_input_id
                        self.next_input_id += 1
                        deferred_inputs.append((token, input_id))
                        if is_verbose:
                            header = f"Pending Input #{input_id}"
                            print(f"\n{header}")
                            print("-" * len(header))
                            print(f"Input token '{token}' arrived")
                            if p0_busy:
                                print("P0 busy")
                            if not interrupts_enabled:
                                print("Interrupts Disabled")
                    else:
                        self.cpu.io_ports[IOPort.P0] = ord(token)
                        self.cpu.io_ports[IOPort.P2] |= 1
                        self.cpu.trap_request = True

                        if is_verbose:
                            print("\nTRAP")
                            print("-----")
                            print("Input token arrived")
                            print(f"P0 <- '{token}'")
                            print("P2.INPUT_READY <- 1")
                            print("Trap Request Raised")

            flags = self.cpu.read_register(int(Register.FLAGS))
            if self.cpu.trap_request and (flags & 0x10) != 0:
                if is_verbose and self.current_resumed_id is not None:
                    print("\nTRAP")
                    print("-----")
                    print(
                        f"Pending Input #{self.current_resumed_id} Accepted")
                    print(f"P0 <- '{self.current_resumed_token}'")
                    print("Trap Request Raised\n")
                    self.current_resumed_id = None

                return_address = self.pipeline.get_interrupt_return_address()
                self.pipeline.flush()
                InterruptController.process_trap(
                    self.cpu, return_pc=return_address)
                self.cpu.trap_request = False

            self.pipeline.tick()
            self.cycle_count += 1

    def print_report(self) -> None:
        if hasattr(sys.stdout, 'silent_global_mute'):
            setattr(sys.stdout, 'silent_global_mute', False)

        print("\n========================================================")
        print("Registers Final State:")
        from src.common.enums import Register
        for reg in Register:
            try:
                val = self.cpu.read_register(int(reg))
            except Exception:
                val = self.cpu.registers[reg]
            print(f"  {reg.name:<5}: {val:<10} (0x{val:08X})")

        accumulated_output = "".join(self.cpu.output_ports[IOPort.P1])

        print("\nPorts Final State")
        print("-----------------")
        print("P0 : empty")
        p1_val = f"'{accumulated_output}'" if accumulated_output else "empty"
        print(f"P1 : {p1_val}")
        print("P2 : INPUT_READY=0")

        print(f"\nAccumulated Output Buffer: {accumulated_output}")
        print(f"Total Simulation Clocks (Latency): {self.cycle_count} cycles")
        print("PipeCore simulation terminated successfully.")
