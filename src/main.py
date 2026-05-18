from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register, IOPort


def main() -> None:
    cpu = CPU()

    # MOV #67, R1
    cpu.memory.write(0x0040, 0x10201000)
    cpu.memory.write(0x0041, 67)
    cpu.memory.write(0x0042, 1)

    # MOV #64, R2
    cpu.memory.write(0x0043, 0x10201000)
    cpu.memory.write(0x0044, 64)
    cpu.memory.write(0x0045, 2)

    # OUT P1, R1
    cpu.memory.write(0x0046, 0x51201000)
    cpu.memory.write(0x0047, int(IOPort.P1))
    cpu.memory.write(0x0048, 1)

    # ADD R1, #-1, R1
    cpu.memory.write(0x0049, 0x20310100)
    cpu.memory.write(0x004A, 1)
    cpu.memory.write(0x004B, 0xFFFFFFFF)
    cpu.memory.write(0x004C, 1)

    # CMP R1, R2
    cpu.memory.write(0x004D, 0x30211000)
    cpu.memory.write(0x004E, 1)
    cpu.memory.write(0x004F, 2)

    # JNZ 0x0046
    cpu.memory.write(0x0050, 0x33100000)
    cpu.memory.write(0x0051, 0x0046)      # Loop Start target address location

    # HALT
    cpu.memory.write(0x0052, 0x01000000)

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
