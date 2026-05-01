# PipeCore Memory Organization

## Memory Architecture

PipeCore follows the **Von Neumann** memory model, where instructions and data share the same address space.

Memory is word-addressable. 

Machine word size: **32 bits**

---

## Memory Layout


| Address Range | Purpose |
|--------------|---------|
| 0x0000 – 0x003F | Interrupt Vector Table (IVT)|
| 0x0040 – 0x0FFF | Program Code |
| 0x1000 – 0x7FFF | Static Data / Heap |
| 0x8000 – 0xFFFF | Stack |

---

## Interrupt Vector Table IVT

Contains addresses of the Interrupt Service Routines (ISRs) / interrupt handlers.

Example:

| Interrupt | Vector Address |
|----------|----------------|
| INT0 | 0x0000 |
| INT1 | 0x0004 |

---

## Program Code

This region stores the executable instructions.

Instructions are variable-length.

The instruction length is determined during decode stage.

---

## Static Data

Holds:

- constants
- string literals
- Pascal-style strings
- global variables

---

## Stack

The Stack grows downward.

Used for storing:

- return addresses
- interrupt state
- temporary data during procedure calls

---

## String Representation

PipeCore uses Pascal strings (pstr).

Format:

[length][char1][char2][char3]...

Each character occupies one machine word.

Example:

"HELLO" → 5, H, E, L, L, O

---

## Memory Design Rationale

This memory model supports:

- trap-based interrupt handling
- procedure execution
- simple string format that’s easy to parse and manipulate
- clear separation of code, data, and stack regions