from src.cpu.datapath import CPU
from src.isa.decoder import decode_opcode
from src.cpu.control_unit import execute
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
