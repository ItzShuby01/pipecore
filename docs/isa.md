# PipeCore ISA

## Processor

PipeCore is a **32-bit pipelined processor based on CISC architecture and built around Von Neumann Memory Model. It uses hardwired control logic and supports interrupt-driven port-mapped I/O**



## Pipeline Structure

PipeCore uses a 3-stage pipeline.

[ Fetch ] → [ Decode ] → [ Execute ]


### Stage 1: Fetch

- reads instruction from memory
- loads instruction into IR
- updates IP


### Stage 2: Decode

- interprets the opcode
- determines instruction length
- resolves addressing modes
- prepares operands



### Stage 3: Execute

- performs ALU operations
- handles memory access
- resolves branches
- writes results back to registers
- executes I/O operations



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



## Port-Mapped I/O

PipeCore uses a simple port-based I/O :

| Port | Purpose |
|------|---------|
| P0 | Input |
| P1 | Output |
| P2 | Status |



## Input Model

Input is **event-driven.**

Each event is represented as:

(addressed_tick, value)

Example:

```(10, 'A')```

At tick 10, value 'A' becomes available.



## Output Model

Output is a buffered stream of symbols.
- Each OUT instruction appends one value
- The output buffer represents the program’s final output

## Addressing Modes

PipeCore supports 5 addressing modes.


### 1. Immediate Addressing

Operand is embedded directly in the instruction.

Syntax:

```asm
#42
```

Example:

```asm
MOV #10, R1
```

### 2. Register Addressing

Operand is stored in a register.

Syntax:

```asm
R2
```

Example:

```asm
ADD R1, R2, R3
```


### 3. Direct Memory Addressing

The instruction specifies the memory address.

Syntax:

```asm
[1000]
```

Example:

```asm
LOAD [1024], R1
```

### 4. Register Indirect Addressing

The specified register holds the memory address of the operand

Syntax:

```asm
[R2]
```
→ **Operand = MEM[R2]**.

Example:

```asm
LOAD [R2], R1
```

### 5. Indexed Addressing

The effective address is computed using a base register and an offset.

→ **Effective Address = Base Register + Offset**

Syntax:

```asm
[R1 + 8]
```

Example:

```asm
LOAD [R1 + 4], R2
```

## Instructions
### 1. Data Movement Instructions

#### MOV
Copies a value from the source to destination.

Syntax:

```asm
MOV src, dst
```
Examples:

```asm
MOV #5, R1
MOV R1, R2
MOV [100], R3
MOV R1, [200]
```

#### LOAD

Loads a value from memory into a register.

Syntax:

```asm
LOAD src, dst
```

Example:

```asm
LOAD [100], R1
```

#### STORE

Puts a register value into memory.

Syntax:

```asm
STORE src, dst
```

Example:

```asm
STORE R1, [100]
```

#### PUSH

Adds register value to the top of stack.

Syntax:

```asm
PUSH R1
```

#### POP
Removes the top of the stack and puts it into register.

Syntax:

```asm
POP R1
```

### 2. Arithmetic Instructions

#### ADD

Adds two operands and stores the result in destination.

Syntax:

```asm
ADD src1, src2, dst
```

Examples:

```asm
ADD R1, R2, R3
ADD [100], #5, R1
```

#### SUB

Subtracts second operand from first and stores the result in destination.

Syntax:

```asm
SUB src1, src2, dst
```

#### MUL

Multiplies two operands and stores the result in destination.

Syntax:

```asm
MUL src1, src2, dst
```

#### DIV
Performs integer division `src1 / src2` and stores the result in destination.

Syntax:

```asm
DIV src1, src2, dst
```

#### MOD
Computes the **remainder** of the division `src1 / src2` and stores the result in destination.

Syntax:

```asm
MOD src1, src2, dst
```

#### INC

Increases operands value by 1 and stores back the result.

Syntax:

```asm
INC dst
```

#### DEC

Decreases operands value by 1 and stores back the result.

Syntax:

```asm
DEC dst
```

### 3. Control Flow Instructions

#### CMP

Compares 2 operands and only updates `FLAGS` without storing the result.

Syntax:

```asm
CMP src1, src2
```

#### JMP (Jump)

Unconditional jump.

Syntax:

```asm
JMP addr
```

#### JZ (Jump if Zero)

Jump to `addr` **if `Z == 1`** .

Syntax:

```asm
JZ addr
```

#### JNZ (Jump if Not Zero)

Jump to `addr` **if `Z == 0`** .

Syntax:

```asm
JNZ addr
```

#### JLT (Jump if Less Than)

Jump to `addr` if **if ` N != V`**.

Syntax:

```asm
JLT addr
```

#### JGT (Jump if Greater Than)

Jump to `addr` **if `Z == 0 && N == V`**.

Syntax:

```asm
JGT addr
```

#### CALL

Transfers control to a procedure.

Syntax:

```asm
CALL addr
```

Behavior:

- Push the **return address** onto stack
- Jump to procedure


#### RET

Returns execution from procedure.

Behavior:

- Pop the **return address** from stack
- Restore it into `IP`


#### IRET

Returns from interrupt handler / Interrupt Service Routine (ISR).

Behavior:

- Restore `FLAGS` from stack.
- Restore `IP` from stack.

### 4. I/O Instructions

#### IN

Reads value from input port into a register.

Syntax:

```asm
IN port, dst
```

Example:

```asm
IN P0, R1
```

#### OUT

Writes value from register to an output port.

Syntax:

```asm
OUT port, src
```

Example:

```asm
OUT P1, R2
```

### 5. System Instructions

#### NOP (No OPeration)

Does nothing for 1 cycle.

Syntax:

```asm
NOP
```

#### HALT

Stops execution.

Syntax:

```asm
HALT
```
