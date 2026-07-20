from __future__ import annotations

import sys
import os
import struct

from src.simulator.simulator import Simulator
from src.simulator.config import load_input_schedule
from src.assembler.translator import Translator as AssemblerTranslator
from src.loader.loader import Loader
from src.translator.alg import Lexer as AlgLexer, Parser as AlgParser
from src.translator.compiler import SemanticAnalyzer, CodeGenerator as AlgCodeGen


def compile_alg_to_asm(alg_path: str) -> str:
    """Compiles a real ALG source file to PipeCore assembly text."""
    if not os.path.exists(alg_path):
        print(f"Error: ALG input file '{alg_path}' could not be found.")
        sys.exit(1)

    with open(alg_path, "r") as f:
        source = f.read()

    try:
        tokens = AlgLexer.tokenize(source)
        ast = AlgParser(tokens).parse_program()

        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        generated_asm = AlgCodeGen(analyzer).generate(ast)
        return str(generated_asm)
    except Exception as e:
        print(f"Compiler Error during ALG translation: {e}")
        sys.exit(1)


def execute_simulation(main_asm: str, isr_asm: str, main_base: str, isr_base: str) -> None:
    try:
        schedule = load_input_schedule("input_schedule.json")
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    simulator = Simulator()
    simulator.initialize_environment(
        main_source=main_asm,
        isr_source=isr_asm,
        input_schedule=schedule,
        main_bin=main_base + ".bin",
        main_lst=main_base + ".lst",
        isr_bin=isr_base + ".bin",
        isr_lst=isr_base + ".lst"
    )
    simulator.run()
    simulator.print_report()


def main() -> None:
    args = sys.argv[1:]
    out_bin = None
    for arg in args:
        if arg.startswith("OUT="):
            out_bin = arg.split("=", 1)[1]
            break

    args = [a for a in args if not a.startswith("OUT=")]

    mode_keywords = {"verbose", "silent", "v", "s"}
    cleaned_args = [a for a in args if not (
        a.startswith("mode=") or a in mode_keywords)]

    if not cleaned_args:
        print("Unknown command. Supported: compile-alg, run-alg, run-asm, run-bin")
        sys.exit(1)

    cmd = cleaned_args[0]

    if cmd == "compile-alg":
        if len(cleaned_args) < 2:
            print(
                "compile-alg requires: make compile-alg <program.alg> [OUT=output.bin]")
            sys.exit(1)

        alg_file = cleaned_args[1]

        if out_bin:
            base_path, _ = os.path.splitext(out_bin)
            asm_file = base_path + ".asm"
            bin_file = out_bin
            lst_file = base_path + ".lst"

            parent_dir = os.path.dirname(out_bin)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
        else:
            base_path, _ = os.path.splitext(alg_file)
            asm_file = base_path + ".asm"
            bin_file = base_path + ".bin"
            lst_file = base_path + ".lst"

        is_isr = "isr" in os.path.basename(alg_file).lower()
        target_start_address = 0x0100 if is_isr else 0x0040

        asm_content = compile_alg_to_asm(alg_file)
        with open(asm_file, "w") as f:
            f.write(asm_content)

        assembler = AssemblerTranslator()
        assembler.assemble(asm_content, start_address=target_start_address,
                           bin_path=bin_file, lst_path=lst_file)
        print(
            f"Compilation successful:\n  {asm_file}\n  {bin_file}\n  {lst_file}")

    elif cmd == "run-alg":
        if len(cleaned_args) < 3:
            print("run-alg requires: run-alg <program.alg> <isr.alg>")
            sys.exit(1)
        main_asm = compile_alg_to_asm(cleaned_args[1])
        isr_asm = compile_alg_to_asm(cleaned_args[2])
        m_base, _ = os.path.splitext(cleaned_args[1])
        i_base, _ = os.path.splitext(cleaned_args[2])
        execute_simulation(main_asm, isr_asm, m_base, i_base)

    elif cmd == "run-asm":
        if len(cleaned_args) < 3:
            print("run-asm requires: run-asm <program.asm> <isr.asm>")
            sys.exit(1)
        if not os.path.exists(cleaned_args[1]) or not os.path.exists(cleaned_args[2]):
            print("Error: Input assembly files could not be found.")
            sys.exit(1)
        with open(cleaned_args[1], "r") as f:
            m_src = f.read()
        with open(cleaned_args[2], "r") as f:
            i_src = f.read()
        m_base, _ = os.path.splitext(cleaned_args[1])
        i_base, _ = os.path.splitext(cleaned_args[2])
        execute_simulation(m_src, i_src, m_base, i_base)

    elif cmd == "run-bin":
        if len(cleaned_args) < 3:
            print("run-bin requires: run-bin <program.bin> <isr.bin>")
            sys.exit(1)

        p_bin, i_bin = cleaned_args[1], cleaned_args[2]
        if not os.path.exists(p_bin) or not os.path.exists(i_bin):
            print("Error: Input binary files could not be found.")
            sys.exit(1)

        try:
            schedule = load_input_schedule("input_schedule.json")
        except Exception as e:
            print(f"Configuration Error: {e}")
            sys.exit(1)

        sim = Simulator()
        sim.cpu.memory.write(0x0000, 0x0100)

        def read_words(path: str) -> list[int]:
            w = []
            with open(path, "rb") as f:
                data = f.read()
                for offset in range(0, len(data), 4):
                    if offset + 4 <= len(data):
                        w.append(struct.unpack(">I", data[offset:offset+4])[0])
            return w

        Loader.load(sim.cpu, read_words(p_bin), start_address=0x0040)
        Loader.load(sim.cpu, read_words(i_bin), start_address=0x0100)

        from src.cpu.pipeline import Pipeline
        sim.pipeline = Pipeline(sim.cpu)
        sim.input_schedule = schedule
        sim.run()
        sim.print_report()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
