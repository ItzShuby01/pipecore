# PipeCore

PipeCore is a custom pipelined CPU simulator inspired by CISC, featuring:
- a custom ISA
- cycle-accurate execution
- a pipelined architecture
- interrupt-driven I/O (traps)
- port-mapped I/O
- a custom high-level programming language and translator

## Characteristics

| Property | Implementation |
|---------|---------------|
| ISA | CISC |
| Control Unit | Hardwired |
| Memory Model | Von Neumann |
| Execution Precision | Tick-accurate |
| Machine Code | Binary |
| I/O Model | Trap-based |
| I/O Addressing | Port-mapped |
| String Format | Pascal strings |
| Pipeline | 3-stage |

## Project Structure

```text
    High-Level ALG Language
        |                                              Interrupt-Driven Input (Trap via P0)
        |                           PipeCore ISA                        |
        |                                 |                             v
        |     +--------------+                           +-----------------------------+
   -----*---->|  Translator  |------------*------------> |       CPU Simulator         |----> Execution Journal
    Algorithm +--------------+       Machine Code        | (Unified Von Neumann Memory)|               
                                       (Binary)          +-----------------------------+
                                                                        |
                                                                        v
                                                                 Output (Port P1)
```
## Running Simulations

### Compile ALG

Compile `.alg` program to `.asm, .bin,` and ,`lst` files:

```bash
make compile-alg <program.alg>
```

Output files:

```text
program.asm
program.bin
program.lst
```

For a custom output path:

```bash
make compile-alg <program.alg> OUT=path/output.bin
```

For ISR programs, use an `isr*.alg` filename. 

### Run ALG

Compile and run a main ALG program with an ISR. 

`run-alg` compiles the ALG source first, then executes the resulting assembly:

```bash
make run-alg <program.alg> <isr.alg>
```

### Run Assembly

Run existing assembly programs:

```bash
make run-asm <program.asm> <isr.asm>
```

### Run Binary

Run existing binary programs:

```bash
make run-bin <program.bin> <isr.bin>
```

### Simulation Modes

Add `mode=` to select the simulation output:

```bash
make run-alg main.alg isr.alg mode=verbose
make run-asm main.asm isr.asm mode=silent
make run-bin main.bin isr.bin mode=v
```

Supported modes:

| Mode           | Description                   |
| -------------- | ----------------------------- |
| `verbose`, `v` | Detailed pipeline trace       |
| `silent`, `s`  | Final simulation results only |
| `default` | Standard simulation report |

Without `mode=`, the `default` trace is displayed.

### Direct Python Usage


```bash
python -m src.main compile-alg <program.alg>
python -m src.main run-alg <program.alg> <isr.alg>
python -m src.main run-asm <program.asm> <isr.asm>
python -m src.main run-bin <program.bin> <isr.bin>
```

## Status

In development
