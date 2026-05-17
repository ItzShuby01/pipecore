from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register


def main() -> None:
    cpu = CPU()

    # MOV #65, R1
    cpu.memory.write(0x0040, 0x10201000)
    cpu.memory.write(0x0041, 65)
    cpu.memory.write(0x0042, 1)

    # HALT
    cpu.memory.write(0x0043, 0x01000000)

    while cpu.running:
        word = cpu.fetch()
        instruction = decode(word, cpu)
        execute(cpu, instruction)

    print("Registers Final State:")
    for reg in Register:
        print(f"{reg.name}: {cpu.registers[reg]}")

    print("PipeCore halted successfully")


if __name__ == "__main__":
    main()
