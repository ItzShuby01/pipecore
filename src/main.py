from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register, IOPort


def main() -> None:
    cpu = CPU()

    # MOV #65, R1
    cpu.memory.write(0x0040, 0x10201000)
    cpu.memory.write(0x0041, 65)
    cpu.memory.write(0x0042, 1)

    # ADD R1, #5, R2
    cpu.memory.write(0x0043, 0x20310100)
    cpu.memory.write(0x0044, 1)
    cpu.memory.write(0x0045, 5)
    cpu.memory.write(0x0046, 2)

    # OUT P1, R2
    cpu.memory.write(0x0047, 0x51201000)
    cpu.memory.write(0x0048, int(IOPort.P1))
    cpu.memory.write(0x0049, 2)

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

    print("PipeCore halted successfully")


if __name__ == "__main__":
    main()
