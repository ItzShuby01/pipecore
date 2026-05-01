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

---

## Project Structure

- src/ — implementation
- tests/ — golden tests
- .github/ — CI configuration

## Status

🚧 In development
