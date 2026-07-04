from __future__ import annotations

from typing import Any, TypedDict
from src.cpu.datapath import CPU
from src.isa.decoder import decode
from src.cpu.control_unit import execute
from src.common.enums import Register


class PipelineStage(TypedDict, total=False):
    pc: int
    word: int
    ins: Any


class Pipeline:
    def __init__(self, cpu: CPU) -> None:
        self.cpu = cpu

        self.if_stage: PipelineStage | None = None
        self.id_stage: PipelineStage | None = None
        self.ex_stage: PipelineStage | None = None
        self.mem_stage: PipelineStage | None = None
        self.wb_stage: PipelineStage | None = None

    def flush(self) -> None:
        """Discards speculative instructions inside IF and ID stages"""
        print("[Pipeline FLUSH] Clearing IF and ID stages due to control flow change.")
        self.if_stage = None
        self.id_stage = None

    def get_interrupt_return_address(self) -> int:
        """Finds the return address to resume execution after an ISR"""
        if self.ex_stage is not None:
            return self.ex_stage["pc"]
        if self.id_stage is not None:
            return self.id_stage["pc"]
        if self.if_stage is not None:
            return self.if_stage["pc"]
        return self.cpu.read_register(int(Register.IP))

    def _halt_in_pipeline(self) -> bool:
        """Checks if HALT instruction is currently in the pipeline"""
        for stage in (self.id_stage, self.ex_stage, self.mem_stage, self.wb_stage):
            if stage is not None:
                ins = stage["ins"]
                opcode_name = getattr(ins.opcode, 'name', str(ins.opcode))
                if opcode_name == "HALT":
                    return True
        return False

    def tick(self) -> None:
        """Advances the 5-stage  pipeline grid by one clock step."""

        # WRITEBACK STAGE (WB)
        if self.wb_stage is not None:
            ins = self.wb_stage["ins"]
            opcode_name = getattr(ins.opcode, 'name', str(ins.opcode))
            if opcode_name == "HALT":
                self.cpu.running = False
            self.wb_stage = None

        # MEMORY STAGE (MEM)
        self.wb_stage = self.mem_stage
        self.mem_stage = None

        # EXECUTE STAGE (EX)
        if self.ex_stage is not None:
            ins = self.ex_stage["ins"]
            ip_before = self.cpu.read_register(int(Register.IP))

            execute(self.cpu, ins)

            ip_after = self.cpu.read_register(int(Register.IP))

            if ip_before != ip_after:
                self.flush()

            self.mem_stage = self.ex_stage
            self.ex_stage = None

        # DECODE STAGE (ID)
        self.ex_stage = self.id_stage
        self.id_stage = None

        # FETCH STAGE (IF)
        if self.if_stage is not None:
            decoded_ins = decode(self.if_stage["word"], self.cpu)
            self.id_stage = {"pc": self.if_stage["pc"], "ins": decoded_ins}
            self.if_stage = None

        #  NEW INSTRUCTION FETCH
        if self.cpu.running and not self._halt_in_pipeline():
            current_pc = self.cpu.read_register(int(Register.IP))
            try:
                word = self.cpu.fetch()
                self.if_stage = {"pc": current_pc, "word": word}
            except Exception:
                self.if_stage = None

        self._log_pipeline_state()

    def _log_pipeline_state(self) -> None:
        def format_stage(stage: PipelineStage | None, is_raw: bool = False) -> str:
            if stage is None:
                return "EMPTY"
            if is_raw:
                return f"{hex(stage['word'])}@0x{stage['pc']:04X}"

            ins = stage["ins"]
            name = "INST"
            if hasattr(ins, 'mnemonic') and ins.mnemonic:
                name = str(ins.mnemonic).upper()
            elif hasattr(ins, 'opcode'):
                name = getattr(ins.opcode, 'name', str(ins.opcode)).upper()
            return f"{name}@0x{stage['pc']:04X}"

        print(
            f"[Pipeline Trace] "
            f"IF: {format_stage(self.if_stage, is_raw=True):<20} | "
            f"ID: {format_stage(self.id_stage):<12} | "
            f"EX: {format_stage(self.ex_stage):<12} | "
            f"MEM: {format_stage(self.mem_stage):<12} | "
            f"WB: {format_stage(self.wb_stage):<12}"
        )

    def is_empty(self) -> bool:
        """Returns True IFF when all 5 processing slots are cleared out."""
        return all(
            stage is None for stage in
            (self.if_stage, self.id_stage, self.ex_stage,
             self.mem_stage, self.wb_stage)
        )
