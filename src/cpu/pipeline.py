from __future__ import annotations

import sys
from typing import Any, TypedDict, TextIO
from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register, Opcode, AddressingMode


class PipelineStage(TypedDict, total=False):
    pc: int
    word: int
    ins: Any


class SimulationOutputFilter:
    def __init__(self, original_stdout: TextIO, mode: str) -> None:
        self.original_stdout = original_stdout
        self.mode = mode
        self.mute_lower_levels = False
        self.last_muted = False

    def write(self, text: str) -> int:
        if self.mute_lower_levels:
            return len(text)

        if self.mode == "silent":
            if any(tag in text for tag in ["[Clock Cycle", "[Pipeline Trace]", "[Pipeline FLUSH]", "[CPU HARDWARE]", "[DEBUG", "[HARDWARE SIGNAL]", "INTERRUPT\n"]):
                self.last_muted = True
                return len(text)

            if self.last_muted and text == "\n":
                self.last_muted = False
                return len(text)

        elif self.mode == "verbose":
            if "[Pipeline Trace]" in text:
                self.last_muted = True
                return len(text)

            if self.last_muted and text == "\n":
                self.last_muted = False
                return len(text)

            if "[HARDWARE SIGNAL]: External Line INT0" in text or "[CPU HARDWARE]: Diverting execution" in text or "[DEBUG INT]: Pushing" in text:
                if "[DEBUG INT]: Pushing" in text:
                    self.original_stdout.write(
                        "\nINTERRUPT\n"
                        "---------\n"
                        "INT0 asserted\n\n"
                        "Context Save\n\n"
                        "SP <- SP-1\n"
                        "MEM[SP] <- FLAGS\n"
                        "SP <- SP-1\n"
                        "MEM[SP] <- PC\n"
                        "PC <- IVT[0]\n"
                    )
                return len(text)

            if "[DEBUG IRET]" in text:
                return len(text)

        self.last_muted = False
        return self.original_stdout.write(text)

    def flush(self) -> None:
        self.original_stdout.flush()


class ContextSilencer:
    def __enter__(self) -> None:
        if isinstance(sys.stdout, SimulationOutputFilter):
            sys.stdout.mute_lower_levels = True

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if isinstance(sys.stdout, SimulationOutputFilter):
            sys.stdout.mute_lower_levels = False


class Pipeline:
    def __init__(self, cpu: CPU) -> None:
        self.cpu = cpu

        self.if_stage: PipelineStage | None = None
        self.id_stage: PipelineStage | None = None
        self.ex_stage: PipelineStage | None = None

        self.empty_streak = 0

        if "silent" in sys.argv or "--silent" in sys.argv:
            self.mode = "silent"
        elif "verbose" in sys.argv or "--verbose" in sys.argv or getattr(cpu, "verbose", False):
            self.mode = "verbose"
        else:
            self.mode = "pipeline"

        sys.stdout = SimulationOutputFilter(sys.stdout, self.mode)

    def flush(self) -> None:
        self.if_stage = None
        self.id_stage = None

    def get_interrupt_return_address(self) -> int:
        if self.ex_stage is not None:
            return self.ex_stage["pc"]
        if self.id_stage is not None:
            return self.id_stage["pc"]
        if self.if_stage is not None:
            return self.if_stage["pc"]
        return self.cpu.read_register(int(Register.IP))

    def _halt_in_pipeline(self) -> bool:
        for stage in (self.id_stage, self.ex_stage):
            if stage is not None:
                ins = stage["ins"]
                opcode_name = getattr(ins.opcode, 'name',
                                      str(ins.opcode)).upper()
                if "HALT" in opcode_name:
                    return True
        return False

    def _peek_opcode_name(self, word: int) -> str:
        try:
            op_val = (word >> 24) & 0xFF
            return Opcode(op_val).name.upper()
        except ValueError:
            return f"OP_{((word >> 24) & 0xFF):02X}"
        except Exception:
            return "UNKNOWN"

    def _get_operand_mode_name(self, op: Any) -> str:
        mode = op.mode
        if mode == AddressingMode.IMMEDIATE:
            return "Immediate"
        elif mode == AddressingMode.REGISTER:
            return "Register"
        elif mode == AddressingMode.DIRECT_MEMORY:
            return "Direct Memory"
        elif mode == AddressingMode.REGISTER_INDIRECT:
            return "Register Indirect"
        elif mode == AddressingMode.INDEXED:
            return "Indexed"
        return "Unknown"

    def _get_operand_str(self, op: Any) -> str:
        mode = op.mode
        if mode == AddressingMode.IMMEDIATE:
            return f"Immediate (#{op.value})"
        elif mode == AddressingMode.REGISTER:
            reg_name = Register(op.value).name if op.value in list(
                Register) else f"R{op.value}"
            return f"Register ({reg_name})"
        elif mode == AddressingMode.DIRECT_MEMORY:
            return f"Direct Memory (MEM[0x{op.value:04X}])"
        elif mode == AddressingMode.REGISTER_INDIRECT:
            reg_name = Register(op.value).name if op.value in list(
                Register) else f"R{op.value}"
            return f"Register Indirect ([{reg_name}])"
        elif mode == AddressingMode.INDEXED:
            return f"Indexed (MEM[{Register(op.value).name} + Offset])"
        return f"Unknown ({op.value})"

    def _get_operand_short_name(self, op: Any) -> str:
        mode = op.mode
        if mode == AddressingMode.IMMEDIATE:
            return f"#{op.value}"
        elif mode == AddressingMode.REGISTER:
            return Register(op.value).name if op.value in list(Register) else f"R{op.value}"
        elif mode == AddressingMode.DIRECT_MEMORY:
            return f"MEM[0x{op.value:04X}]"
        elif mode == AddressingMode.REGISTER_INDIRECT:
            reg_name = Register(op.value).name if op.value in list(
                Register) else f"R{op.value}"
            return f"[{reg_name}]"
        elif mode == AddressingMode.INDEXED:
            return f"[{Register(op.value).name}+Offset]"
        return f"op_{op.value}"

    def _resolve_operand_value(self, op: Any) -> int:
        mode = op.mode
        if mode == AddressingMode.IMMEDIATE:
            return int(op.value)
        elif mode == AddressingMode.REGISTER:
            return int(self.cpu.read_register(op.value))
        elif mode == AddressingMode.DIRECT_MEMORY:
            try:
                return int(self.cpu.memory.read(op.value))
            except Exception:
                return 0
        elif mode == AddressingMode.REGISTER_INDIRECT:
            try:
                addr = int(self.cpu.read_register(op.value))
                return int(self.cpu.memory.read(addr))
            except Exception:
                return 0
        return int(op.value)

    def _generate_dynamic_id_details(self, ins: Any, word: int) -> str:
        opcode_name = getattr(ins.opcode, 'name', str(ins.opcode)).upper()

        size = 1
        if any(op.mode in (AddressingMode.IMMEDIATE, AddressingMode.DIRECT_MEMORY, AddressingMode.INDEXED) for op in ins.operands):
            size = 3 if opcode_name in ("MOV", "CALL") else 2

        lines = [
            "ID",
            "--",
            f"Instruction   : {opcode_name}",
            f"Opcode        : {opcode_name} (0x{ins.opcode.value:02X})",
            f"Length        : {size} words",
            "",
            "Operand Decode",
            "--------------"
        ]

        if not ins.operands:
            lines.append("None")
        else:
            if len(ins.operands) == 1:
                lines.append(f"SRC : {self._get_operand_str(ins.operands[0])}")
            elif len(ins.operands) >= 2:
                lines.append(f"SRC : {self._get_operand_str(ins.operands[0])}")
                lines.append(f"DST : {self._get_operand_str(ins.operands[1])}")

        return "\n".join(lines)

    def _generate_dynamic_ex_details(self, ins: Any, pc: int) -> str:
        opcode_name = getattr(ins.opcode, 'name', str(ins.opcode)).upper()
        lines = [
            "EX",
            "--",
            "",
            f"Instruction : {opcode_name}",
            ""
        ]

        if ins.opcode in (Opcode.MOV, Opcode.IN, Opcode.OUT):
            lines.extend([
                "Datapath",
                "--------"
            ])
            if len(ins.operands) >= 2:
                src_op = ins.operands[0]
                dst_op = ins.operands[1]
                val = self._resolve_operand_value(src_op)
                dst_short = self._get_operand_short_name(dst_op)

                lines.extend([
                    f"Source      : {self._get_operand_mode_name(src_op)}",
                    f"Destination : {self._get_operand_short_name(dst_op)}",
                    "",
                    "Memory",
                    "------",
                    "None",
                    "",
                    "Writeback",
                    "---------",
                    f"{dst_short} <- {val}"
                ])
            else:
                lines.append("Transfer Actions Completed")

        elif ins.opcode == Opcode.LOAD:
            if len(ins.operands) >= 2:
                src_op = ins.operands[0]
                dst_op = ins.operands[1]
                addr = src_op.value if src_op.mode == AddressingMode.DIRECT_MEMORY else self._resolve_operand_value(
                    src_op)
                val = self._resolve_operand_value(src_op)
                dst_short = self._get_operand_short_name(dst_op)

                lines.extend([
                    "Datapath",
                    "--------",
                    f"Address = 0x{addr:04X}",
                    "",
                    "Memory",
                    "------",
                    f"MEM[0x{addr:04X}] -> {val}",
                    "",
                    "Writeback",
                    "---------",
                    f"{dst_short} <- {val}"
                ])

        elif ins.opcode == Opcode.STORE:
            if len(ins.operands) >= 2:
                src_op = ins.operands[0]
                dst_op = ins.operands[1]
                addr = dst_op.value if dst_op.mode == AddressingMode.DIRECT_MEMORY else self._resolve_operand_value(
                    dst_op)
                src_short = self._get_operand_short_name(src_op)

                lines.extend([
                    "Datapath",
                    "--------",
                    f"Address = 0x{addr:04X}",
                    "",
                    "Memory",
                    "------",
                    f"MEM[0x{addr:04X}] <- {src_short}",
                    "",
                    "Writeback",
                    "---------",
                    "None"
                ])

        elif ins.opcode in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD, Opcode.CMP, Opcode.INC, Opcode.DEC):
            lines.extend([
                "ALU",
                "---"
            ])

            if len(ins.operands) >= 2:
                src_op = ins.operands[0]
                dst_op = ins.operands[1]
                val_a = self._resolve_operand_value(dst_op)
                val_b = self._resolve_operand_value(src_op)
                dst_short = self._get_operand_short_name(dst_op)

                res = val_a
                op_char = "?"
                if ins.opcode == Opcode.ADD:
                    res = val_a + val_b
                    op_char = "+"
                elif ins.opcode in (Opcode.SUB, Opcode.CMP):
                    res = val_a - val_b
                    op_char = "-"
                elif ins.opcode == Opcode.MUL:
                    res = val_a * val_b
                    op_char = "*"
                elif ins.opcode == Opcode.DIV:
                    res = val_a // val_b if val_b != 0 else 0
                    op_char = "/"
                elif ins.opcode == Opcode.MOD:
                    res = val_a % val_b if val_b != 0 else 0
                    op_char = "%"

                lines.append(f"{val_a} {op_char} {val_b} = {res}")

                if ins.opcode != Opcode.CMP:
                    lines.extend([
                        "",
                        "Writeback",
                        "---------",
                        f"{dst_short} <- {res}"
                    ])

            elif len(ins.operands) == 1:
                op = ins.operands[0]
                val = self._resolve_operand_value(op)
                op_short = self._get_operand_short_name(op)

                res = val + 1 if ins.opcode == Opcode.INC else val - 1
                op_char = "+ 1" if ins.opcode == Opcode.INC else "- 1"

                lines.append(f"{val} {op_char} = {res}")
                lines.extend([
                    "",
                    "Writeback",
                    "---------",
                    f"{op_short} <- {res}"
                ])

        elif ins.opcode in (Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JLT, Opcode.JGT, Opcode.CALL, Opcode.RET):
            lines.extend([
                "Branch",
                "------"
            ])

            flags = self.cpu.read_register(int(Register.FLAGS))
            z_flag = flags & 1

            if ins.opcode in (Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JLT, Opcode.JGT):
                taken = True
                if ins.opcode == Opcode.JZ:
                    taken = (z_flag == 1)
                elif ins.opcode == Opcode.JNZ:
                    taken = (z_flag == 0)

                if taken and len(ins.operands) > 0:
                    lines.append(f"PC <- 0x{ins.operands[0].value:04X}")
                else:
                    lines.append("PC <- Next Sequential PC")

                if taken:
                    lines.extend([
                        "",
                        "Pipeline",
                        "--------",
                        "Flush IF",
                        "Flush ID"
                    ])

            elif ins.opcode == Opcode.CALL:
                if len(ins.operands) > 0:
                    lines.append(f"PC <- 0x{ins.operands[0].value:04X}")
                lines.extend([
                    "",
                    "Pipeline",
                    "--------",
                    "Flush IF",
                    "Flush ID"
                ])
            elif ins.opcode == Opcode.RET:
                sp = self.cpu.read_register(int(Register.SP))
                try:
                    ret_addr = self.cpu.memory.read(sp)
                    lines.append(f"PC <- 0x{ret_addr:04X}")
                except Exception:
                    lines.append("PC <- Stack Return Address")
                lines.extend([
                    "",
                    "Pipeline",
                    "--------",
                    "Flush IF",
                    "Flush ID"
                ])

        elif ins.opcode == Opcode.IRET:
            lines.extend([
                "Stack Restore",
                "-------------",
                "FLAGS <- MEM[SP]",
                "PC    <- MEM[SP+1]",
                "SP    <- SP + 2",
                "",
                "Pipeline",
                "--------",
                "Flush IF",
                "Flush ID"
            ])

        elif ins.opcode in (Opcode.PUSH, Opcode.POP):
            lines.extend([
                "Stack Operation",
                "---------------"
            ])
            if len(ins.operands) > 0:
                op = ins.operands[0]
                val = self._resolve_operand_value(op)
                op_short = self._get_operand_short_name(op)
                sp = self.cpu.read_register(int(Register.SP))
                if ins.opcode == Opcode.PUSH:
                    lines.extend([
                        f"MEM[0x{(sp - 1) & 0xFFFF:04X}] <- {val}",
                        f"SP <- 0x{(sp - 1) & 0xFFFF:04X}"
                    ])
                else:
                    lines.extend([
                        f"{op_short} <- MEM[0x{sp:04X}]",
                        f"SP <- 0x{(sp + 1) & 0xFFFF:04X}"
                    ])

        elif ins.opcode in (Opcode.HALT, Opcode.NOP):
            lines.extend([
                "System Control",
                "--------------"
            ])
            if ins.opcode == Opcode.HALT:
                lines.extend([
                    "HALT asserted",
                    "Pipeline draining"
                ])
            else:
                lines.append("No Operation")

        return "\n".join(lines).strip()

    def tick(self) -> None:
        if_verbose: str | None = None
        id_verbose: str | None = None
        ex_verbose: str | None = None

        current_if = self.if_stage
        current_id = self.id_stage
        current_ex = self.ex_stage

        flushed = False
        if current_ex is not None:
            ins = current_ex["ins"]
            opcode_name = getattr(ins.opcode, 'name', str(ins.opcode)).upper()

            if self.mode == "verbose":
                ex_verbose = self._generate_dynamic_ex_details(
                    ins, current_ex["pc"])

            if "HALT" in opcode_name:
                self.cpu.running = False
            else:
                ip_before = self.cpu.read_register(int(Register.IP))

                with ContextSilencer():
                    execute(self.cpu, ins)

                ip_after = self.cpu.read_register(int(Register.IP))

                if ip_before != ip_after:
                    self.flush()
                    flushed = True

        if flushed:
            self.ex_stage = None
            self.id_stage = None
        else:
            self.ex_stage = current_id

            if current_if is not None:
                with ContextSilencer():
                    decoded_ins = decode(current_if["word"], self.cpu)

                self.id_stage = {"pc": current_if["pc"], "ins": decoded_ins}
                if self.mode == "verbose":
                    id_verbose = self._generate_dynamic_id_details(
                        decoded_ins, current_if["word"])
            else:
                self.id_stage = None

        if self.cpu.running and not self._halt_in_pipeline():
            current_pc = self.cpu.read_register(int(Register.IP))
            try:
                with ContextSilencer():
                    word = self.cpu.fetch()

                self.if_stage = {"pc": current_pc, "word": word}

                if self.mode == "verbose":
                    op_name = self._peek_opcode_name(word)

                    if_verbose = (
                        "IF\n"
                        "--\n\n"
                        f"PC      : 0x{current_pc:04X}\n"
                        f"Opcode  : {op_name}\n"
                        f"Word    : 0x{word:08X}"
                    )
            except Exception:
                self.if_stage = None
        else:
            self.if_stage = None

        if self.is_empty():
            self.empty_streak += 1
            if self.empty_streak > 32:
                self.cpu.running = False
        else:
            self.empty_streak = 0

        self._log_pipeline_state(if_verbose, id_verbose, ex_verbose)

    def _log_pipeline_state(self, if_v: str | None = None, id_v: str | None = None, ex_v: str | None = None) -> None:
        def format_stage(stage: PipelineStage | None, is_raw: bool = False) -> str:
            if stage is None:
                return "EMPTY"
            if is_raw:
                return f"0x{stage['word']:08X}@0x{stage['pc']:04X}"

            ins = stage["ins"]
            name = "INST"
            if hasattr(ins, 'mnemonic') and ins.mnemonic:
                name = str(ins.mnemonic).upper()
            elif hasattr(ins, 'opcode'):
                name = getattr(ins.opcode, 'name', str(ins.opcode)).upper()
            return f"{name}@0x{stage['pc']:04X}"

        def format_short_stage(stage: PipelineStage | None) -> str:
            if stage is None:
                return "EMPTY"

            addr = f" @0x{stage['pc']:04X}" if 'pc' in stage else ""

            if "ins" in stage:
                ins = stage["ins"]
                if hasattr(ins, 'mnemonic') and ins.mnemonic:
                    return f"{str(ins.mnemonic).upper()}{addr}"
                return f"{getattr(ins.opcode, 'name', 'INST').upper()}{addr}"
            elif "word" in stage:
                op_name = self._peek_opcode_name(stage["word"])
                return f"{op_name}{addr}"
            return "EMPTY"

        if self.mode == "verbose":
            print("\nPipeline Registers")
            print("---------")
            print(f"IF : {format_short_stage(self.if_stage)}")
            print(f"ID : {format_short_stage(self.id_stage)}")
            print(f"EX : {format_short_stage(self.ex_stage)}")
            print()
            if if_v:
                print(if_v + "\n")
            if id_v:
                print(id_v + "\n")
            if ex_v:
                print(ex_v + "\n")
            print("========================================================\n")
        else:
            print(
                f"[Pipeline Trace] "
                f"IF: {format_stage(self.if_stage, is_raw=True):<25} | "
                f"ID: {format_stage(self.id_stage):<15} | "
                f"EX: {format_stage(self.ex_stage):<15}"
            )

    def is_empty(self) -> bool:
        return all(stage is None for stage in (self.if_stage, self.id_stage, self.ex_stage))
