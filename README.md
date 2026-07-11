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

### Using Make (Recommended)

```bash
make run <main_program.asm> <isr_program.asm> mode=[verbose|silent|v|s]
```


### Using Python

```bash
python -m src.main <main_program.asm> <isr_program.asm> mode=[verbose|silent|v|s]
```
Optional modes:


| Mode | Description | Example (Make) | Example (Python) |
|------|-------------|----------------|------------------|
| Default | Standard pipeline simulation | `make run main.asm isr.asm` | `python -m src.main main.asm isr.asm` |
| Verbose (`verbose` / `v`) | Detailed pipeline trace for every clock cycle (tick) | `make run main.asm isr.asm mode=verbose` | `python -m src.main main.asm isr.asm mode=v` |
| Silent (`silent` / `s`) | Display only the final simulation results | `make run main.asm isr.asm mode=s` | `python -m src.main main.asm isr.asm mode=silent` |



## Status

In development
