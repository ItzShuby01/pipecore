from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register, IOPort


def main() -> None:
    cpu = CPU()

    # MOV #1337, R1
    cpu.memory.write(0x0040, 0x10201000)
    cpu.memory.write(0x0041, 1337)
    cpu.memory.write(0x0042, 1)

    # PUSH R1
    cpu.memory.write(0x0043, 0x13110000)
    cpu.memory.write(0x0044, 1)

    # MOV #0, R1
    cpu.memory.write(0x0045, 0x10201000)
    cpu.memory.write(0x0046, 0)
    cpu.memory.write(0x0047, 1)

    # POP R1
    cpu.memory.write(0x0048, 0x14110000)
    cpu.memory.write(0x0049, 1)

    # HALT
    cpu.memory.write(0x004A, 0x01000000)

    while cpu.running:
        word = cpu.fetch()
        instruction = decode(word, cpu)
        execute(cpu, instruction)

    print("Registers Final State:")
    for reg in Register:
        val = cpu.registers[reg]
        print(f"  {reg.name:<5}: {val:<10} (0x{val:08X})")

    print("\n--- Port-Mapped I/O Terminal ---")
    output_string = "".join(cpu.output_ports[IOPort.P1])
    print(f"Port {IOPort.P1.name} Output: '{output_string}'")

    print("\n--- Stack Memory ---")
    print(f"Value left at 0xFFFE: {cpu.memory.read(0xFFFE)}")
    print("PipeCore halted successfully")


if __name__ == "__main__":
    main()
