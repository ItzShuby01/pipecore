from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register


def main() -> None:
    cpu = CPU()

    # IVT
    cpu.memory.write(0x0000, 0x0050)  # Point INT0 to handler at 0x0050

    # MOV #10, R1
    cpu.memory.write(0x0040, 0x10201000)
    cpu.memory.write(0x0041, 10)
    cpu.memory.write(0x0042, 1)

    # NOP
    cpu.memory.write(0x0043, 0x00000000)

    # HALT
    cpu.memory.write(0x0044, 0x01000000)

    cpu.memory.write(0x0050, 0x10201000)
    cpu.memory.write(0x0051, 255)
    cpu.memory.write(0x0052, 3)

    # IRET
    cpu.memory.write(0x0053, 0x42000000)

    cycle_count = 0

    while cpu.running:
        # Simulate external hardware event firing on cycle 1
        if cycle_count == 1:
            print("[HARDWARE SIGNAL]: Line INT0 pulled HIGH!")
            cpu.interrupt_asserted = 0  # Assert INT0

        if cpu.running and cpu.interrupt_asserted is not None:
            intr_num = cpu.interrupt_asserted
            cpu.interrupt_asserted = None

            current_flags = cpu.read_register(int(Register.FLAGS))
            current_ip = cpu.read_register(int(Register.IP))
            current_sp = cpu.read_register(int(Register.SP))

            current_sp = (current_sp - 1) & 0xFFFF
            cpu.memory.write(current_sp, current_flags)

            current_sp = (current_sp - 1) & 0xFFFF
            cpu.memory.write(current_sp, current_ip)

            cpu.write_register(int(Register.SP), current_sp)

            target_isr_address = cpu.memory.read(intr_num)
            cpu.write_register(int(Register.IP), target_isr_address)
            print(
                f"[CPU HARDWARE]: Diverting execution context to ISR at 0x{target_isr_address:04X}")

        # Normal Pipeline Processing
        word = cpu.fetch()
        instruction = decode(word, cpu)
        execute(cpu, instruction)
        cycle_count += 1

    print("\nRegisters Final State:")
    for reg in Register:
        val = cpu.registers[reg]
        print(f"  {reg.name:<5}: {val:<10} (0x{val:08X})")

    print("\n--- Interrupt Verification ---")
    print(
        f"Main program execution state (R1 should be 10): {cpu.registers[Register.R1]}")
    print(
        f"ISR execution state (R3 should be 255): {cpu.registers[Register.R3]}")
    print("PipeCore halted successfully")


if __name__ == "__main__":
    main()
