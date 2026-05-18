from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register, IOPort


def main() -> None:
    cpu = CPU()

    # CALL 0x0046
    cpu.memory.write(0x0040, 0x40100000)
    cpu.memory.write(0x0041, 0x0046)

    # HALT
    cpu.memory.write(0x0042, 0x01000000)

    # SUBROUTINE
    # MOV #42, R3
    cpu.memory.write(0x0046, 0x10201000)
    cpu.memory.write(0x0047, 42)
    cpu.memory.write(0x0048, 3)

    # RET
    cpu.memory.write(0x0049, 0x41000000)

    while cpu.running:
        word = cpu.fetch()
        instruction = decode(word, cpu)
        execute(cpu, instruction)

    print("Registers Final State:")
    for reg in Register:
        val = cpu.registers[reg]
        print(f"  {reg.name:<5}: {val:<10} (0x{val:08X})")

    # print("\n--- Port-Mapped I/O Terminal ---")
    # output_string = "".join(cpu.output_ports[IOPort.P1])
    # print(f"Port {IOPort.P1.name} Output: '{output_string}'")

    # print("\n--- Stack Memory ---")
    # print(f"Value left at 0xFFFE: {cpu.memory.read(0xFFFE)}")

    print("\n--- Procedure Verification ---")
    print(f"Subroutine Execution Check: {cpu.registers[Register.R3]}")
    print("PipeCore halted successfully")


if __name__ == "__main__":
    main()
