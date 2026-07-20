from __future__ import annotations

import sys
from typing import Any, TypedDict, TextIO
from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register, Opcode, AddressingMode, IOPort


class PipelineStage(TypedDict, total=False):
    pc: int
    word: int
    ins: Any
    words: list[int]
    size: int


class SimulationOutputFilter:
    """Filters and re-formats stdout traces dynamically based on execution mode."""

    def __init__(self, original_stdout: TextIO, mode: str, pipeline: Pipeline) -> None:
        self.original_stdout = original_stdout
        self.mode = mode
        self.pipeline = pipeline
        self.mute_lower_levels = False
        self.last_muted = False
        self._v_sp = 0xFFFF

    def write(self, text: str) -> int:
        if self.mute_lower_levels:
            return len(text)

        if self.mode == "silent":
            if any(tag in text for tag in ["[Clock Cycle", "[Pipeline Trace]", "TRAP", "Context Save", "restored"]):
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

        if "Context Save" in text:
            try:
                self._v_sp = self.pipeline.cpu.read_register(int(Register.SP))
            except Exception:
                self._v_sp = 0xFFFF

        if "SP <- SP-1" in text:
            v_next = (self._v_sp - 4) & 0xFFFF
            text = text.replace(
                "SP <- SP-1", f"SP : {self._v_sp:04X} -> {v_next:04X}")
            self._v_sp = v_next

        if "MEM[SP] <- IP" in text:
            text = text.replace(
                "MEM[SP] <- IP", f"MEM[{self._v_sp:04X}] <- IP")

        if "MEM[SP] <- FLAGS" in text:
            text = text.replace("MEM[SP] <- FLAGS",
                                f"MEM[{self._v_sp:04X}] <- FLAGS")

        if "FLAGS.I <- 0" in text:
            text = text.replace("FLAGS.I <- 0", "FLAGS.I : 1 -> 0")

        if "IP <- MEM[IVT[0]]" in text:
            if "Pipeline Flush" not in text:
                text += (
                    "\n\nPipeline Flush\n"
                    "--------------\n"
                    "IF <- EMPTY\n"
                    "ID <- EMPTY"
                )

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
        self._out_buffer = ""
        self._final_reported = False

        if "silent" in sys.argv or "s" in sys.argv:
            self.mode = "silent"
        elif "verbose" in sys.argv or "v" in sys.argv or getattr(cpu, "verbose", False):
            self.mode = "verbose"
        else:
            self.mode = "pipeline"

        sys.stdout = SimulationOutputFilter(sys.stdout, self.mode, self)

        if self.cpu.running:
            current_pc = self.cpu.read_register(int(Register.IP))
            try:
                with ContextSilencer():
                    word = self.cpu.fetch()

                size = 1
                words = [word]
                try:
                    with ContextSilencer():
                        saved_ip = self.cpu.read_register(int(Register.IP))
                        temp_ins = decode(word, self.cpu, base_pc=current_pc)
                        self.cpu.write_register(int(Register.IP), saved_ip)

                    if temp_ins is not None:
                        size = 1 + getattr(temp_ins, 'operand_count', 0)

                        for i in range(1, size):
                            try:
                                words.append(
                                    int(self.cpu.memory.read(current_pc + i * 4)))
                            except Exception:
                                words.append(0)
                except Exception:
                    pass

                self.if_stage = {"pc": current_pc,
                                 "word": word, "words": words, "size": size}
                self.cpu.write_register(
                    int(Register.IP), current_pc + 4 * size)
            except Exception:
                self.if_stage = None

    def flush(self) -> None:
        self.if_stage = None
        self.id_stage = None
        self.ex_stage = None

    def get_interrupt_return_address(self) -> int:
        if self.ex_stage is not None:
            return self.ex_stage["pc"]
        if self.id_stage is not None:
            return self.ex_stage["pc"] if self.ex_stage else self.id_stage["pc"]
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
        elif getattr(mode, 'name', '') == "DIRECT_MEMORY" or getattr(mode, 'value', -1) == 2:
            return "Direct Memory"
        elif getattr(mode, 'name', '') == "REGISTER_INDIRECT" or getattr(mode, 'value', -1) == 3:
            return "Register Indirect"
        elif getattr(mode, 'name', '') == "INDEXED" or getattr(mode, 'value', -1) == 4:
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
        elif getattr(mode, 'name', '') == "DIRECT_MEMORY" or getattr(mode, 'value', -1) == 2:
            return f"Direct Memory (MEM[0x{op.value:04X}])"
        elif getattr(mode, 'name', '') == "REGISTER_INDIRECT" or getattr(mode, 'value', -1) == 3:
            reg_name = Register(op.value).name if op.value in list(
                Register) else f"R{op.value}"
            return f"Register Indirect ([{reg_name}])"
        elif getattr(mode, 'name', '') == "INDEXED" or getattr(mode, 'value', -1) == 4:
            base_reg_idx = (op.value >> 16) & 0xFFFF
            offset = op.value & 0xFFFF
            if offset & 0x8000:
                offset -= 0x10000
            reg_name = Register(base_reg_idx).name if base_reg_idx in list(
                Register) else f"R{base_reg_idx}"
            sign = "+" if offset >= 0 else ""
            return f"Indexed (MEM[{reg_name} {sign} {offset}])"
        return f"Unknown ({op.value})"

    def _get_operand_short_name(self, op: Any) -> str:
        mode = op.mode
        if mode == AddressingMode.IMMEDIATE:
            return f"#{op.value}"
        elif mode == AddressingMode.REGISTER:
            return Register(op.value).name if op.value in list(Register) else f"R{op.value}"
        elif getattr(mode, 'name', '') == "DIRECT_MEMORY" or getattr(mode, 'value', -1) == 2:
            return f"MEM[0x{op.value:04X}]"
        elif getattr(mode, 'name', '') == "REGISTER_INDIRECT" or getattr(mode, 'value', -1) == 3:
            reg_name = Register(op.value).name if op.value in list(
                Register) else f"R{op.value}"
            return f"[{reg_name}]"
        elif getattr(mode, 'name', '') == "INDEXED" or getattr(mode, 'value', -1) == 4:
            base_reg_idx = (op.value >> 16) & 0xFFFF
            offset = op.value & 0xFFFF
            if offset & 0x8000:
                offset -= 0x10000
            reg_name = Register(base_reg_idx).name if base_reg_idx in list(
                Register) else f"R{base_reg_idx}"
            sign = "+" if offset >= 0 else ""
            return f"[{reg_name}{sign}{offset}]"
        return f"op_{op.value}"

    def _resolve_operand_value(self, op: Any) -> int:
        mode = op.mode
        if mode == AddressingMode.IMMEDIATE:
            return int(op.value)
        elif mode == AddressingMode.REGISTER:
            return int(self.cpu.read_register(op.value))
        elif getattr(mode, 'name', '') == "DIRECT_MEMORY" or getattr(mode, 'value', -1) == 2:
            try:
                return int(self.cpu.memory.read(op.value))
            except Exception:
                return 0
        elif getattr(mode, 'name', '') == "REGISTER_INDIRECT" or getattr(mode, 'value', -1) == 3:
            try:
                addr = int(self.cpu.read_register(op.value))
                return int(self.cpu.memory.read(addr))
            except Exception:
                return 0
        elif getattr(mode, 'name', '') == "INDEXED" or getattr(mode, 'value', -1) == 4:
            try:
                addr = self._get_effective_address(op)
                return int(self.cpu.memory.read(addr))
            except Exception:
                return 0
        return int(op.value)

    def _get_effective_address(self, op: Any) -> int:
        mode = op.mode
        if getattr(mode, 'name', '') == "DIRECT_MEMORY" or getattr(mode, 'value', -1) == 2:
            return int(op.value)
        elif getattr(mode, 'name', '') == "REGISTER_INDIRECT" or getattr(mode, 'value', -1) == 3:
            return int(self.cpu.read_register(op.value))
        elif getattr(mode, 'name', '') == "INDEXED" or getattr(mode, 'value', -1) == 4:
            base_reg = (op.value >> 16) & 0xFFFF
            offset = op.value & 0xFFFF
            if offset & 0x8000:
                offset -= 0x10000
            return int((self.cpu.read_register(base_reg) + offset) & 0xFFFF)
        return int(op.value)

    def _generate_dynamic_id_details(self, ins: Any, word: int) -> str:
        opcode_name = getattr(ins.opcode, 'name', str(ins.opcode)).upper()
        size = 1 + getattr(ins, 'operand_count', 0)

        lines = [
            "ID",
            "--",
            f"Instruction   : {opcode_name}",
            f"Opcode        : {opcode_name} (0x{ins.opcode.value:02X})",
            f"Length        : {size} words",
            ""
        ]

        if opcode_name == "IN":
            lines.extend([
                "Operands",
                "--------",
                "Port : P0",
                f"Dest : {self._get_operand_short_name(ins.operands[1]) if len(ins.operands) > 1 else 'R1'}"
            ])
        elif opcode_name == "OUT":
            lines.extend([
                "Operands",
                "--------",
                "Port : P1",
                f"Source : {self._get_operand_short_name(ins.operands[1]) if len(ins.operands) > 1 else 'R1'}"
            ])
        else:
            lines.extend([
                "Operand Decode",
                "--------------"
            ])
            if not ins.operands:
                lines.append("None")
            else:
                if len(ins.operands) == 3 and ins.opcode in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD):
                    lines.append(
                        f"SRC1 : {self._get_operand_str(ins.operands[0])}")
                    lines.append(
                        f"SRC2 : {self._get_operand_str(ins.operands[1])}")
                    lines.append(
                        f"DST  : {self._get_operand_str(ins.operands[2])}")
                elif len(ins.operands) == 1:
                    lines.append(
                        f"SRC : {self._get_operand_str(ins.operands[0])}")
                elif len(ins.operands) >= 2:
                    lines.append(
                        f"SRC : {self._get_operand_str(ins.operands[0])}")
                    lines.append(
                        f"DST : {self._get_operand_str(ins.operands[1])}")

        return "\n".join(lines)

    def _generate_dynamic_ex_details(self, ins: Any, pc: int) -> str:
        opcode_name = getattr(ins.opcode, 'name', str(ins.opcode)).upper()

        if ins.opcode == Opcode.IRET:
            try:
                sp = self.cpu.read_register(int(Register.SP))
                ip_after = self.cpu.memory.read((sp - 4) & 0xFFFF)
            except Exception:
                ip_after = 0
            return (
                "EX\n"
                "--\n"
                f"Instruction : {opcode_name}\n\n"
                "FLAGS restored\n"
                "IP restored\n"
                "FLAGS.I : 0 -> 1\n\n"
                f"Returning to 0x{ip_after:04X}"
            )

        lines = [
            "EX",
            "--",
            f"Instruction : {opcode_name}",
        ]

        if ins.opcode == Opcode.IN:
            dst_short = self._get_operand_short_name(
                ins.operands[1]) if len(ins.operands) > 1 else "R1"
            port_val = self.cpu.io_ports.get(IOPort.P0, 0)
            char_repr = f" ('{chr(port_val)}')" if 32 <= port_val <= 126 else ""

            lines.extend([
                "Port        : P0",
                f"Dest        : {dst_short}",
                "",
                f"{dst_short} <- P0{char_repr}",
                "P2.INPUT_READY <- 0"
            ])

        elif ins.opcode == Opcode.OUT:
            src_short = self._get_operand_short_name(
                ins.operands[1]) if len(ins.operands) > 1 else "R1"
            reg_idx = ins.operands[1].value if len(
                ins.operands) > 1 else int(Register.R1)
            reg_val = self.cpu.read_register(reg_idx)
            char_repr = f" ('{chr(reg_val)}')" if 32 <= reg_val <= 126 else ""
            val_raw = chr(reg_val) if 32 <= reg_val <= 126 else str(reg_val)

            if 32 <= reg_val <= 126:
                self._out_buffer += chr(reg_val)

            lines.extend([
                "Port        : P1",
                f"Source      : {src_short}",
                "",
                f"P1 <- {src_short}{char_repr}",
                "",
                "Output Buffer",
                "-------------",
                f"{self._out_buffer if self._out_buffer else val_raw}"
            ])

        elif ins.opcode == Opcode.MOV:
            if len(ins.operands) >= 2:
                src_op = ins.operands[0]
                dst_op = ins.operands[1]
                val = self._resolve_operand_value(src_op)
                dst_short = self._get_operand_short_name(dst_op)
                lines.extend([
                    "",
                    f"Source      : {self._get_operand_mode_name(src_op)}",
                    f"Destination : {dst_short}",
                    f"{dst_short} <- {val}"
                ])
            else:
                lines.extend(["", "Transfer Actions Completed"])

        elif ins.opcode == Opcode.LOAD:
            if len(ins.operands) >= 2:
                src_op = ins.operands[0]
                dst_op = ins.operands[1]
                addr = self._get_effective_address(src_op)
                val = self._resolve_operand_value(src_op)
                dst_short = self._get_operand_short_name(dst_op)
                lines.extend([
                    "",
                    f"Address : 0x{addr:04X}",
                    f"MEM[0x{addr:04X}] -> {val}",
                    f"{dst_short} <- {val}"
                ])

        elif ins.opcode == Opcode.STORE:
            if len(ins.operands) >= 2:
                src_op = ins.operands[0]
                dst_op = ins.operands[1]
                addr = self._get_effective_address(dst_op)
                src_short = self._get_operand_short_name(src_op)
                lines.extend([
                    "",
                    f"Address : 0x{addr:04X}",
                    f"MEM[0x{addr:04X}] <- {src_short}"
                ])

        elif ins.opcode in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD, Opcode.CMP, Opcode.INC, Opcode.DEC):
            lines.extend([""])
            if len(ins.operands) == 3 and ins.opcode in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD):
                src1_op = ins.operands[0]
                src2_op = ins.operands[1]
                dst_op = ins.operands[2]

                val_1 = self._resolve_operand_value(src1_op)
                val_2 = self._resolve_operand_value(src2_op)
                dst_short = self._get_operand_short_name(dst_op)

                res = val_1
                op_char = "?"
                if ins.opcode == Opcode.ADD:
                    res, op_char = val_1 + val_2, "+"
                elif ins.opcode == Opcode.SUB:
                    res, op_char = val_1 - val_2, "-"
                elif ins.opcode == Opcode.MUL:
                    res, op_char = val_1 * val_2, "*"
                elif ins.opcode == Opcode.DIV:
                    res, op_char = (val_1 // val_2 if val_2 != 0 else 0), "/"
                elif ins.opcode == Opcode.MOD:
                    res, op_char = (val_1 % val_2 if val_2 != 0 else 0), "%"

                lines.append(f"{val_1} {op_char} {val_2} = {res}")
                lines.append(f"{dst_short} <- {res}")
            elif len(ins.operands) >= 2:
                src_op = ins.operands[0]
                dst_op = ins.operands[1]
                val_a = self._resolve_operand_value(dst_op)
                val_b = self._resolve_operand_value(src_op)
                dst_short = self._get_operand_short_name(dst_op)

                if ins.opcode == Opcode.CMP:
                    res = val_b - val_a
                    lines.append(f"{val_b} - {val_a} = {res}")
                else:
                    res = val_a
                    lines.append(f"{val_a} ? {val_b} = {res}")
                    lines.append(f"{dst_short} <- {res}")
            elif len(ins.operands) == 1:
                op = ins.operands[0]
                post_val = self._resolve_operand_value(op)
                op_short = self._get_operand_short_name(op)

                if ins.opcode == Opcode.INC:
                    pre_val = post_val - 1
                    lines.append(f"{pre_val} + 1 = {post_val}")
                else:
                    pre_val = post_val + 1
                    lines.append(f"{pre_val} - 1 = {post_val}")

                lines.append(f"{op_short} <- {post_val}")

        elif ins.opcode in (Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JLT, Opcode.JGT, Opcode.CALL, Opcode.RET):
            lines.extend([""])
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
                    lines.extend(["Flush IF", "Flush ID"])

            elif ins.opcode == Opcode.CALL:
                current_sp = self.cpu.read_register(int(Register.SP))
                try:
                    ret_addr = self.cpu.memory.read(current_sp)
                except Exception:
                    ret_addr = 0

                target = ins.operands[0].value if len(ins.operands) > 0 else 0

                lines.extend([
                    f"Push return address: 0x{ret_addr:04X}",
                    f"MEM[0x{current_sp:04X}] <- 0x{ret_addr:04X}",
                    f"SP <- 0x{current_sp:04X}",
                    "",
                    f"PC <- 0x{target:04X}",
                    "Flush IF",
                    "Flush ID"
                ])

            elif ins.opcode == Opcode.RET:
                current_sp = self.cpu.read_register(int(Register.SP))
                old_sp = (current_sp - 4) & 0xFFFF
                try:
                    ret_addr = self.cpu.memory.read(old_sp)
                except Exception:
                    ret_addr = 0

                lines.extend([
                    f"Pop return address: 0x{ret_addr:04X}",
                    f"SP <- 0x{current_sp:04X}",
                    "",
                    f"PC <- 0x{ret_addr:04X}",
                    "Flush IF",
                    "Flush ID"
                ])

        elif ins.opcode in (Opcode.PUSH, Opcode.POP):
            lines.extend([""])
            if len(ins.operands) > 0:
                op = ins.operands[0]
                val = self._resolve_operand_value(op)
                op_short = self._get_operand_short_name(op)
                current_sp = self.cpu.read_register(int(Register.SP))

                if ins.opcode == Opcode.PUSH:
                    lines.extend([
                        f"MEM[0x{current_sp:04X}] <- {val}",
                        f"SP <- 0x{current_sp:04X}"
                    ])
                else:
                    source_addr = (current_sp - 4) & 0xFFFF
                    lines.extend([
                        f"{op_short} <- MEM[0x{source_addr:04X}]",
                        f"SP <- 0x{current_sp:04X}"
                    ])

        elif ins.opcode in (Opcode.HALT, Opcode.NOP):
            lines.extend([""])
            if ins.opcode == Opcode.HALT:
                lines.extend(["HALT asserted", "Pipeline draining"])
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

            if "HALT" in opcode_name:
                self.cpu.running = False
            else:
                setattr(self.cpu, "current_instruction_pc", current_ex["pc"])
                ip_before = self.cpu.read_register(int(Register.IP))

                with ContextSilencer():
                    execute(self.cpu, ins)

                ip_after = self.cpu.read_register(int(Register.IP))

                branch_taken = False
                if ins.opcode in (Opcode.JMP, Opcode.CALL, Opcode.RET, Opcode.IRET):
                    branch_taken = True
                elif ins.opcode in (Opcode.JZ, Opcode.JNZ, Opcode.JLT, Opcode.JGT):
                    flags = self.cpu.read_register(int(Register.FLAGS))
                    z = bool(flags & (1 << 0))
                    n = bool(flags & (1 << 1))
                    v = bool(flags & (1 << 3))
                    if ins.opcode == Opcode.JZ and z:
                        branch_taken = True
                    elif ins.opcode == Opcode.JNZ and not z:
                        branch_taken = True
                    elif ins.opcode == Opcode.JLT and (n != v):
                        branch_taken = True
                    elif ins.opcode == Opcode.JGT and (not z and (n == v)):
                        branch_taken = True

                if branch_taken or ip_before != ip_after:
                    self.flush()
                    flushed = True

        if flushed:
            self.ex_stage = None
            self.id_stage = None
        else:
            self.ex_stage = current_id

            if current_if is not None:
                with ContextSilencer():
                    saved_pipeline_ip = self.cpu.read_register(
                        int(Register.IP))
                    self.cpu.write_register(
                        int(Register.IP), current_if["pc"] + 4)

                    decoded_ins = decode(
                        current_if["word"], self.cpu, base_pc=current_if["pc"])

                    self.cpu.write_register(
                        int(Register.IP), saved_pipeline_ip)

                self.id_stage = {
                    "pc": current_if["pc"], "ins": decoded_ins, "word": current_if["word"]}
            else:
                self.id_stage = None

        if self.cpu.running and not self._halt_in_pipeline():
            current_pc = self.cpu.read_register(int(Register.IP))
            try:
                with ContextSilencer():
                    word = self.cpu.fetch()

                size = 1
                words = [word]
                try:
                    with ContextSilencer():
                        saved_ip = self.cpu.read_register(int(Register.IP))
                        temp_ins = decode(word, self.cpu, base_pc=current_pc)
                        self.cpu.write_register(int(Register.IP), saved_ip)

                    if temp_ins is not None:
                        size = 1 + getattr(temp_ins, 'operand_count', 0)

                        for i in range(1, size):
                            try:
                                words.append(
                                    int(self.cpu.memory.read(current_pc + i * 4)))
                            except Exception:
                                words.append(0)
                except Exception:
                    pass

                self.if_stage = {"pc": current_pc,
                                 "word": word, "words": words, "size": size}
                self.cpu.write_register(
                    int(Register.IP), current_pc + 4 * size)
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

        if self.mode == "verbose":
            if current_if is not None:
                op_name = self._peek_opcode_name(current_if["word"])
                size = current_if.get("size", 1)
                words = current_if.get("words", [current_if["word"]])
                lines = [
                    "IF",
                    "--",
                    f"PC       : 0x{current_if['pc']:04X}",
                    f"Opcode   : {op_name}",
                    f"Length   : {size} {'words' if size > 1 else 'word'}",
                ]
                for i, w in enumerate(words):
                    lines.append(f"Word[{i}]  : 0x{w:08X}")
                if_verbose = "\n".join(lines)
            else:
                if_verbose = "IF\n--\nNo instruction"

            if current_id is not None:
                id_verbose = self._generate_dynamic_id_details(
                    current_id["ins"], current_id["word"])
            else:
                id_verbose = "ID\n--\nNo instruction"

            if current_ex is not None:
                ex_verbose = self._generate_dynamic_ex_details(
                    current_ex["ins"], current_ex["pc"])
            else:
                ex_verbose = "EX\n--\nNo instruction"

        self._log_pipeline_state(
            if_verbose, id_verbose, ex_verbose, current_if, current_id, current_ex)

    def _log_pipeline_state(self, if_v: str | None = None, id_v: str | None = None, ex_v: str | None = None,
                            snap_if: PipelineStage | None = None, snap_id: PipelineStage | None = None, snap_ex: PipelineStage | None = None) -> None:
        def format_stage(stage: PipelineStage | None, is_raw: bool = False) -> str:
            if stage is None:
                return "EMPTY"
            if is_raw:
                return f"0x{stage['word']:08X}@0x{stage['pc']:04X}"
            ins = stage["ins"]
            name = str(ins.mnemonic).upper() if hasattr(ins, 'mnemonic') and ins.mnemonic else getattr(
                ins.opcode, 'name', str(ins.opcode)).upper()
            return f"{name}@0x{stage['pc']:04X}"

        def format_short_stage(stage: PipelineStage | None) -> str:
            if stage is None:
                return "EMPTY"
            addr = f" @0x{stage['pc']:04X}" if 'pc' in stage else ""
            if "ins" in stage:
                ins = stage["ins"]
                name = str(ins.mnemonic).upper() if hasattr(
                    ins, 'mnemonic') and ins.mnemonic else getattr(ins.opcode, 'name', 'INST').upper()
                return f"{name}{addr}"
            elif "word" in stage:
                return f"{self._peek_opcode_name(stage['word'])}{addr}"
            return "EMPTY"

        if self.mode == "verbose":
            print("\nPipeline Registers")
            print("------------------")
            print(f"IF : {format_short_stage(snap_if)}")
            print(f"ID : {format_short_stage(snap_id)}")
            print(f"EX : {format_short_stage(snap_ex)}")
            print()
            if if_v:
                print(if_v + "\n")
            if id_v:
                print(id_v + "\n")
            if ex_v:
                print(ex_v + "\n")
            print("-------------------------------------------------\n")
        else:
            print(
                f"[Pipeline Trace] "
                f"IF: {format_stage(snap_if, is_raw=True):<25} | "
                f"ID: {format_stage(snap_id):<15} | "
                f"EX: {format_stage(snap_ex):<15}"
            )

    def is_empty(self) -> bool:
        return all(stage is None for stage in (self.if_stage, self.id_stage, self.ex_stage))
