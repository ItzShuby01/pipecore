# PipeCore Register Architecture

## Register Model

The processor contains 8 registers : 4 general-purpose registers and 4 special-purpose registers.

## General-Purpose Registers
- R0 (preferably used as a temporary register during arithmetic operations)
- R1 
- R2 
- R3

All four registers can be used interchangeably in arithmetic and memory operations.

The translator often uses R0 for intermediate results when evaluating expressions. However, this is just a convention — PipeCore itself does not enforce any accumulator-based limitations.



## Special-Purpose Registers

### Instruction Pointer (IP)

Holds the address of the next instruction to be executed.

It is updated during:

- normal execution
- jumps
- procedure calls
- interrupt handling

### Stack Pointer (SP)

Always points to top of the stack.

Used for:

- procedure calls
- returning from procedure
- saving interrupt state
- interrupt restoration

### Instruction Register (IR)

Stores the instruction currently being executed.

Used during:

- decode stage
- execution stage
- inspection of pipeline state

### FLAGS Register

Keeps track of processor status

| Flag | Meaning |
|------|---------|
| Z | Zero |
| N | Negative |
| C | Carry |
| O | Overflow |
| I | Interrupt Enable |

