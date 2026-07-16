from __future__ import annotations

import sys
import os
from typing import Any
from src.simulator.simulator import Simulator
from src.simulator.config import load_input_schedule


def main() -> None:
    flag_keywords = {"verbose", "silent", "v", "s"}
    non_flags = [a for a in sys.argv[1:] if a not in flag_keywords]

    if len(non_flags) < 2:
        print(
            "Usage: python -m src.main <main_program.asm> <isr_program.asm> mode=[verbose/silent/v/s]")
        sys.exit(1)

    main_path = non_flags[0]
    isr_path = non_flags[1]

    if not os.path.exists(main_path) or not os.path.exists(isr_path):
        print("Error: Input assembly files could not be found.")
        sys.exit(1)

    with open(main_path, "r") as f:
        main_program = f.read()

    with open(isr_path, "r") as f:
        isr_program = f.read()

    main_base, _ = os.path.splitext(main_path)
    isr_base, _ = os.path.splitext(isr_path)

    try:
        schedule = load_input_schedule("input_schedule.json")
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    simulator = Simulator()
    simulator.initialize_environment(
        main_source=main_program,
        isr_source=isr_program,
        input_schedule=schedule,
        main_bin=main_base + ".bin",
        main_lst=main_base + ".lst",
        isr_bin=isr_base + ".bin",
        isr_lst=isr_base + ".lst"
    )
    simulator.run()
    simulator.print_report()


if __name__ == "__main__":
    main()
