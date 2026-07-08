from __future__ import annotations

from src.simulator.simulator import Simulator


def main() -> None:
    main_program = """
    LOOP:
        NOP
        JMP LOOP
    """

    isr_program = """
    IN P0, R1
    OUT P1, R1
    IRET
    """

    schedule = [
        (5, 'H'),
        (6, 'i'),
        (7, 'm')
    ]

    simulator = Simulator()
    simulator.initialize_environment(
        main_source=main_program,
        isr_source=isr_program,
        input_schedule=schedule
    )
    simulator.run()
    simulator.print_report()


if __name__ == "__main__":
    main()
