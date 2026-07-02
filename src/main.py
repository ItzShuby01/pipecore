from __future__ import annotations
from src.simulator.simulator import Simulator


def main() -> None:
    main_program = """
    MOV #10, R1
    NOP
    HALT
    """

    isr_program = """
    MOV #255, R3
    IRET
    """

    simulator = Simulator()
    simulator.initialize_environment(main_program, isr_program)
    simulator.run()
    simulator.print_report()


if __name__ == "__main__":
    main()
