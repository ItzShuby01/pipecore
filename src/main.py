from src.simulator.cpu import CPU
from src.simulator.decoder import decode_opcode
from src.simulator.instructions import execute
from src.common.enums import Opcode


def main() -> None:
    cpu = CPU()

    halt_instruction = Opcode.HALT << 24
    cpu.memory.write(0x0040, halt_instruction)

    while cpu.running:
        word = cpu.fetch()
        opcode = decode_opcode(word)
        execute(cpu, opcode)

    print("PipeCore halted successfully")


if __name__ == "__main__":
    main()
