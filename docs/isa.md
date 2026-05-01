# PipeCore ISA

## Processor

PipeCore is a **32-bit pipelined processor based on CISC architecture and built around Von Neumann Memory Model. It uses hardwired control logic and supports interrupt-driven port-mapped I/O**

---


## Pipeline Structure

PipeCore uses a 3-stage pipeline.

[ Fetch ] → [ Decode ] → [ Execute ]

---

### Stage 1: Fetch

- reads instruction from memory
- loads instruction into IR
- updates IP

---

### Stage 2: Decode

- interprets the opcode
- determines instruction length
- resolves addressing modes
- prepares operands

This stage introduces CISC decoding complexity.

---

### Stage 3: Execute

- performs ALU operations
- handles memory access
- resolves branches
- writes results back to registers
- executes I/O operations

---

## Interrupt Model

PipeCore uses vectored hardware interrupts.

What happens on an interrupt:

1. Current instruction completes
2. IP is pushed onto stack
3. FLAGS is pushed onto stack
4. Interrupt disabled
5. Handler / ISR (Interrupt Service Routine) address loaded from IVT is set as new IP
6. ISR executes
7. IRET restores state

---

## Port-Mapped I/O

PipeCore uses a simple port-based I/O :

| Port | Purpose |
|------|---------|
| P0 | Input |
| P1 | Output |
| P2 | Status |

---

## Input Model

Input is **event-driven.**

Each event is represented as:

(addressed_tick, value)

Example:

(10, 'A')

At tick 10, value 'A' becomes available.

---

## Output Model

Output is a buffered stream of symbols.
- Each OUT instruction appends one value
- The output buffer represents the program’s final output

---

## Instruction Encoding

PipeCore uses **variable-length instructions**, which is typical for CISC.

Instruction size depends on:

- operation code (opcode)
- number of operands
- addressing mode

Supported sizes:

- 1 word
- 2 words
- 3 words
- 4 words

---
