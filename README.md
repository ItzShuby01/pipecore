# PipeCore

* **ФИО:** Идрис Шуаибу
* **Группа:** P3231
* **Вариант:**

```text
alg | cisc | neum | hw | tick | binary | trap | port | pstr | prob1 | pipeline
```

## Table of Contents

1. [Overview and Structure](#overview-and-structure)
2. [Project Structure](#project-structure)
3. [Language](#language)

   * [ALG Language](#alg-language)
   * [Syntax](#syntax)
   * [Semantics](#semantics)
   * [Scope](#scope)
   * [Data Types](#data-types)
   * [Literals](#literals)
   * [Variables and Assignment](#variables-and-assignment)
   * [Control Flow](#control-flow)
   * [Procedures](#procedures)
   * [Input and Output](#input-and-output)
   * [Interrupt Handler](#interrupt-handler)
4. [Memory Organization](#memory-organization)

   * [Memory Architecture](#memory-architecture)
   * [Memory Layout](#memory-layout)
   * [Program and Data Mapping](#program-and-data-mapping)
   * [Procedure Mapping](#procedure-mapping)
   * [Interrupt Mapping](#interrupt-mapping)
5. [Instruction Set](#instruction-set)

   * [Processor](#processor)
   * [Registers](#registers)
   * [Addressing Modes](#addressing-modes)
   * [Instructions](#instructions)
   * [Instruction Encoding](#instruction-encoding)
   * [Port-Mapped I/O](#port-mapped-io)
   * [Interrupt System](#interrupt-system)
6. [Translator](#translator)

   * [Command-Line Interface](#command-line-interface)
   * [Compilation](#compilation)
7. [Processor Model](#processor-model)

   * [Input and Output](#input-and-output-1)
   * [DataPath](#datapath)
   * [Control Unit](#control-unit)
   * [Interrupt Processing](#interrupt-processing)
   * [Simulation](#simulation)
8. [Testing](#testing)

   * [Test Organization](#test-organization)
   * [Golden Tests](#golden-tests)
   * [Input Schedule](#input-schedule)
9. [Pipeline](#pipeline)
10. [Example Toolchain](#example-toolchain)
11. [Documentation](#documentation)

---

# Overview and Structure

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

---

# Language

## ALG Language

ALG language supports:

* variables and assignment;
* integer arithmetic;
* comparison operations;
* conditional statements;
* `while` loops;
* procedures and procedure calls;
* character and string literals;
* input and output;
* interrupt handlers.

---

## Syntax


```bnf
<program> ::= { <declaration> | <statement> }

<declaration> ::= <variable-declaration>
                 | <procedure-declaration>
                 | <interrupt-declaration>

<variable-declaration> ::= "var" <identifier> [ ":" <type> ] ";"

<procedure-declaration> ::= "procedure" <identifier>
                            "(" [ <parameter-list> ] ")"
                            "{"
                                { <declaration> | <statement> }
                            "}"

<parameter-list> ::= <parameter> { "," <parameter> }

<parameter> ::= <identifier> ":" <type>

<interrupt-declaration> ::= "interrupt" "input"
                            "{"
                                { <declaration> | <statement> }
                            "}"

<statement> ::= <assignment>
              | <if-statement>
              | <while-statement>
              | <return-statement>
              | <expression-statement>
              | <block>

<block> ::= "{"
                { <declaration> | <statement> }
            "}"

<assignment> ::= <identifier> ":=" <expression> ";"

<if-statement> ::= "if" "(" <expression> ")" <block>
                   [ "else" <block> ]

<while-statement> ::= "while" "(" <expression> ")" <block>

<return-statement> ::= "return" [ <expression> ] ";"

<expression-statement> ::= <expression> ";"

<expression> ::= <literal>
               | <identifier>
               | <binary-expression>
               | <unary-expression>
               | <call-expression>
               | <input-expression>
               | <output-expression>

<binary-expression> ::= <expression> <binary-operator> <expression>

<binary-operator> ::= "+"
                    | "-"
                    | "*"
                    | "/"
                    | "%"
                    | "=="
                    | "!="
                    | "<"
                    | "<="
                    | ">"
                    | ">="

<unary-expression> ::= "-" <expression>

<call-expression> ::= <identifier>
                      "(" [ <argument-list> ] ")"

<argument-list> ::= <expression> { "," <expression> }

<input-expression> ::= "input" "()"

<output-expression> ::= "output" "(" <expression> ")"

<type> ::= "int"
         | "char"
         | "string"
         | "boolean"

<literal> ::= <integer-literal>
            | <character-literal>
            | <string-literal>
            | <boolean-literal>

<integer-literal> ::= <digit> { <digit> }

<character-literal> ::= "'" <character> "'"

<string-literal> ::= "\"" { <string-character> } "\""

<boolean-literal> ::= "true"
                     | "false"

<identifier> ::= <letter> { <letter> | <digit> | "_" }

<digit> ::= "0" | "1" | "2" | "3" | "4"
          | "5" | "6" | "7" | "8" | "9"

<letter> ::= "a" | "b" | ... | "z"
           | "A" | "B" | ... | "Z"
```

---

## Semantics

### Evaluation Strategy

Uses eager evaluation.

* Expressions are evaluated before their results are used.
* Operands are evaluated from left to right.
* Arithmetic operators follow the defined precedence.
* A `while` condition is evaluated before every iteration.
* Procedure arguments are evaluated before the procedure call.
* `return <expression>;` evaluates the expression and returns its value.
* `return;` terminates the procedure without a return value.

Operator precedence, from highest to lowest:

1. unary minus;
2. multiplication, division, remainder;
3. addition and subtraction;
4. comparison operators.

```text
- x
* / %
+ -
== != < <= > >=
```

Integer division is signed integer division.

Comparison operators produce a `boolean` result.

---

## Scope

Uses lexical block scope.

* A variable is visible from its declaration to the end of its block.
* Variables declared inside a block are not visible outside it.
* Procedure parameters and local variables are accessible only inside the procedure.
* An inner declaration may hide an outer variable with the same name.
* Global variables are visible throughout the program after their declaration.

---

## Data Types

| Type      | Description                                           |
| --------- | ----------------------------------------------------- |
| `int`     | Signed 32-bit integer                                 |
| `char`    | One character represented by its character code       |
| `string`  | Sequence of characters stored in Pascal-string format |
| `boolean` | Logical truth value                                   |

A variable has a fixed type after declaration.

Assignments and operands must have compatible types.

---

## Literals

| Literal   | Example         | Type      |
| --------- | --------------- | --------- |
| Integer   | `42`, `-10`     | `int`     |
| Character | `'A'`, `'!'`    | `char`    |
| String    | `"HELLO"`       | `string`  |
| Boolean   | `true`, `false` | `boolean` |

Character literals are represented by character codes.

Strings use Pascal-style representation:

```text
[length] [character 1] [character 2] ...
```
---


## Variables and Assignment

Variables are declared using `var`:

```text
var x: int;
var c: char;
var text: string;
```

Assignment uses `:=`:

```text
x := 10;
x := x + 5;
```

The right-hand side is evaluated first, then the result is assigned to the variable.

---

## Control Flow

### Conditional

```text
if (condition) {
    statements
} else {
    statements
}
```

The condition is evaluated before selecting the branch.

### While Loop

```text
while (condition) {
    statements
}
```

The condition is evaluated before every iteration.

---

## Procedures

Procedures are declared using:

```text
procedure name(parameters) {
    statements
}
```

Example:

```text
procedure add(a: int, b: int) {
    return a + b;
}
```

A procedure is called using:

```text
add(10, 20);
```

A returned value may be used in an expression:

```text
var result: int;

result := add(10, 20);

output(result);
```

---

## Input and Output

ALG provides:

```text
input()
output(value)
```

Input is read through port `P0`.

Output is written through port `P1`.

```text
output('A');
```

```text
output("HELLO");
```

For a string, characters are sent to `P1` sequentially.

Each output operation appends one character to the simulator's output buffer. The final contents of the buffer are displayed after simulation.


---

## Interrupt Handler

Input interrupt handler is declared as:

```text
interrupt input {
    statements
}
```

---

# Memory Organization

## Memory Architecture

PipeCore uses a **Von Neumann** memory model.

Memory is byte-addressable.

The machine word is:

```text
32 bits = 4 bytes
```

The Program Counter points to the first byte of the next instruction.

After decoding an instruction, the sequential IP update is:

```text
IP := IP + instruction_length_words × 4
```

unless the instruction changes control flow.

---

## Memory Layout

| Address Range     | Purpose                |
| ----------------- | ---------------------- |
| `0x0000 – 0x003F` | Interrupt Vector Table |
| `0x0040 – 0x0FFF` | Program Code           |
| `0x1000 – 0x7FFF` | Static Data / Heap     |
| `0x8000 – 0xFFFF` | Stack                  |

---


## Program and Data Mapping


```text
              Memory
+--------------------------------+
| IVT                            |
+--------------------------------+
| Program code                   |
| main program                   |
| procedure bodies               |
| ISR                            |
+--------------------------------+
| Static data                    |
| string literals                |
| global variables               |
| constants / heap               |
+--------------------------------+
|                                |
| Stack                          |
| ↓ grows downward               |
+--------------------------------+
```

The program code is placed in the code region beginning at `0x0040`.

The stack is used for procedure return addresses and interrupts.

---



## Procedure Mapping

```text
      Caller
        |
        | **CALL** procedure
        v
+----------------+
| Procedure      |
|                |
| ...            |
|                |
| RET            |
+----------------+
        |
        v
 Caller continues
```

---

## Interrupt Mapping

The input interrupt uses:

```text
INT0
Vector address: 0x0000
```

When an interrupt is accepted:

```text
current execution
       |
       v
complete instruction
       |
       v
push IP
       |
       v
push FLAGS
       |
       v
disable interrupts
       |
       v
load ISR address from IVT
       |
       v
execute ISR
       |
       v
IRET
       |
       v
restore FLAGS and IP
```

---

# Instruction Set (ISA)

## Processor

Instructions may occupy:

* 1 word;
* 2 words;
* 3 words;
* 4 words.

The instruction length depends on:

* opcode;
* operand count;
* addressing modes;
* operand encoding.

---

## Registers

### General-Purpose

| Register | Purpose                                                          |
| -------- | ---------------------------------------------------------------- |
| `R0`     | General-purpose / commonly used for temporary expression results |
| `R1`     | General-purpose                                                  |
| `R2`     | General-purpose                                                  |
| `R3`     | General-purpose                                                  |

All 4 general-purpose registers can be used for arithmetic and memory operations.

### Special-Purpose

| Register | Purpose                |
| -------- | ---------------------- |
| `IP`     | Instruction Pointer    |
| `SP`     | Stack Pointer          |
| `IR`     | Instruction Register   |
| `FLAGS`  | Processor status flags |

### FLAGS

| Flag | Meaning          |
| ---- | ---------------- |
| `Z`  | Zero             |
| `N`  | Negative         |
| `C`  | Carry            |
| `O`  | Overflow         |
| `I`  | Interrupt Enable |

---

## Addressing Modes


### Immediate

The value is embedded in the instruction.

```asm
MOV #10, R1
```

### Register

The operand is contained in a register.

```asm
ADD R1, R2, R3
```

### Direct Memory

The instruction contains a memory address.

```asm
LOAD [1024], R1
```

### Register Indirect

The register contains the memory address.

```asm
LOAD [R2], R1
```

Equivalent to:

```text
operand = MEM[R2]
```

### Indexed

The effective address is calculated using a register and an offset.

```asm
LOAD [R1 + 4], R2
```

Effective address:

```text
EA = R1 + 4
```

---

## Instructions

Uses AT&T syntax:

```text
instruction source, destination
```

### Data Movement

```asm
MOV src, dst
LOAD src, dst
STORE src, dst
PUSH R1
POP R1
```

### Arithmetic

```asm
ADD src1, src2, dst
SUB src1, src2, dst
MUL src1, src2, dst
DIV src1, src2, dst
MOD src1, src2, dst
INC dst
DEC dst
```

### Control Flow

```asm
CMP src1, src2
JMP addr
JZ addr
JNZ addr
JLT addr
JGT addr
CALL addr
RET
IRET
```

Conditions:

```text
JZ   : Z == 1
JNZ  : Z == 0
JLT  : N != O
JGT  : Z == 0 && N == O
```

`CMP` updates `FLAGS` without storing the result.

### I/O

```asm
IN P0, R1
OUT P1, R1
```

### System

```asm
NOP
HALT
```

---

# Instruction Encoding

Every instruction begins with a fixed 32-bit header.

The header is followed by zero or more operand words.

```text
[ Header (32 bits) ] [ Operand 1 ] [ Operand 2 ] [ Operand 3 ]
```

The decoder reads the header to determine:

* opcode;
* operand count;
* addressing modes.

## Header Format

| Bits    | Field             |
| ------- | ----------------- |
| `31–24` | Opcode            |
| `23–20` | Operand Count     |
| `19–16` | Addressing Mode 1 |
| `15–12` | Addressing Mode 2 |
| `11–8`  | Addressing Mode 3 |
| `7–0`   | Reserved          |

## Addressing Mode Encoding

| Mode              | Code  |
| ----------------- | ----- |
| Immediate         | `0x0` |
| Register          | `0x1` |
| Direct Memory     | `0x2` |
| Register Indirect | `0x3` |
| Indexed           | `0x4` |

## Register Encoding

| Register | Code  |
| -------- | ----- |
| `R0`     | `0x0` |
| `R1`     | `0x1` |
| `R2`     | `0x2` |
| `R3`     | `0x3` |
| `IP`     | `0x4` |
| `SP`     | `0x5` |
| `IR`     | `0x6` |
| `FLAGS`  | `0x7` |

## Port Encoding

| Port | Code  |
| ---- | ----- |
| `P0` | `0x0` |
| `P1` | `0x1` |
| `P2` | `0x2` |

## Flag Encoding

| Flag | Bit |
| ---- | --- |
| `Z`  | `0` |
| `N`  | `1` |
| `C`  | `2` |
| `O`  | `3` |
| `I`  | `4` |

## Instruction Size Examples

| Instruction            | Size    |
| ---------------------- | ------- |
| `HALT`                 | 1 word  |
| `INC R1`               | 2 words |
| `MOV #5, R1`           | 3 words |
| `ADD [100], [200], R3` | 4 words |

---


# Port-Mapped I/O

PipeCore uses port-based I/O.

| Port | Purpose     |
| ---- | ----------- |
| `P0` | Input Data  |
| `P1` | Output Data |
| `P2` | Status      |

## P2 Status

| Bit | Name          | Meaning                                                   |
| --- | ------------- | --------------------------------------------------------- |
| `0` | `INPUT_READY` | No unread input when `0`; unread input available when `1` |

---

# Interrupt System

Input is interrupt-driven.

Simulator reads scheduled input events from:

```text
input_schedule.json
```

Example:

```json
{
    "events": [
        {
            "tick": 10,
            "token": "A"
        }
    ]
}
```

At tick `10`, the simulator:

1. writes `A` to `P0`;
2. sets `P2.INPUT_READY` to `1`;
3. asserts an interrupt request.

The CPU does not know about the schedule itself.

After completing the current instruction, the CPU:

1. pushes `IP`;
2. pushes `FLAGS`;
3. clears `FLAGS.I`;
4. reads the ISR address from the IVT;
5. executes the ISR;
6. returns using `IRET`.

Interrupts are disabled while the ISR is executing.

If another input event occurs during the ISR, it remains pending and may be accepted after `IRET` restores the previous processor state.

---

# Translator

## Command-Line Interface

### Input

* ALG source file;
* assembly source file;
* binary program;
* ISR source/binary;
* optional simulation mode;
* optional output path.

### Output

Compilation produces:

```text
program.asm
program.bin
program.lst
```

---

## Compilation

Compile ALG:

```bash
make compile-alg <program.alg>
```

Direct Python usage:

```bash
python -m src.main compile-alg <program.alg>
```

A custom binary output path can be specified with:

```bash
make compile-alg <program.alg> OUT=path/output.bin
```

For ISR programs, an `isr*.alg` filename is used.

---

## Running ALG

```bash
make run-alg <program.alg> <isr.alg>
```

The command translates the ALG source and then runs the resulting program.

---

## Running Assembly

```bash
make run-asm <program.asm> <isr.asm>
```

---

## Running Binary

```bash
make run-bin <program.bin> <isr.bin>
```

---

## Simulation Modes

The simulator supports:

| Mode           | Description                   |
| -------------- | ----------------------------- |
| `verbose`, `v` | Detailed pipeline trace       |
| `silent`, `s`  | Final simulation results only |
| `default`      | Standard simulation report    |

Example:

```bash
make run-alg main.alg isr.alg mode=verbose
```

---


# Processor Model

## Input and Output

The processor simulator accepts:

* a machine-code program;
* ISR machine code;
* an external input schedule.

Example:

```bash
make run-bin program.bin isr.bin
```

---

## DataPath

The datapath performs:

* instruction transfer from memory;
* register reads and writes;
* arithmetic and logical operations;
* address calculation;
* memory access;
* flag updates;
* control-flow updates.

---

## Control Unit

The Control Unit is **hardwired**. 

It controls the 3 stages:

```text
Fetch → Decode → Execute
```

---

## Processor Registers

```text
R0 R1 R2 R3
IP SP IR FLAGS
```

`IP` = address of the next instruction.

`SP` = the top of the stack.

`IR` = the current instruction.

`FLAGS` stores processor status and interrupt-enable information.

---

## Interrupt Processing

```text
Input Schedule
      |
      v
    P0/P2
      |
      v
Interrupt Request
      |
      v
Interrupt Controller
      |
      v
     CPU
      |
      +--> Push IP
      |
      +--> Push FLAGS
      |
      +--> Disable interrupts
      |
      +--> Load ISR from IVT
      |
      v
     ISR
      |
      v
    IRET
```

---

## Simulation

The simulation includes:

* instruction fetching;
* decoding;
* execution;
* register updates;
* memory operations;
* pipeline state;
* input events;
* interrupt processing;
* output operations.

---

# Testing

## Test Organization


```text
tests/
├── cases/
│   ├── 01_hello/
│   │   ├── hello.alg
│   │   ├── hello.asm
│   │   ├── hello.bin
│   │   └── hello.lst
│   │
│   └── 02_cat/
│       ├── 02_cat.alg
│       ├── 02_cat.asm
│       ├── 02_cat.bin
│       └── 02_cat.lst
│
└── golden/
    ├── 01_hello.yml
    └── 02_cat.yml
```

---

## Golden Tests

### `hello`

Files:

* [`hello.alg`](./tests/cases/01_hello/hello.alg)
* [`hello.asm`](./tests/cases/01_hello/hello.asm)
* [`hello.bin`](./tests/cases/01_hello/hello.bin)
* [`hello.lst`](./tests/cases/01_hello/hello.lst)
* [`01_hello.yml`](./tests/golden/01_hello.yml)

Golden test:

[`tests/golden/01_hello.yml`](./tests/golden/01_hello.yml)

---

### `cat`

Files:

* [`02_cat.alg`](./tests/cases/02_cat/02_cat.alg)
* [`02_cat.asm`](./tests/cases/02_cat/02_cat.asm)
* [`02_cat.bin`](./tests/cases/02_cat/02_cat.bin)
* [`02_cat.lst`](./tests/cases/02_cat/02_cat.lst)
* [`02_cat.yml`](./tests/golden/02_cat.yml)

Golden test:

[`tests/golden/02_cat.yml`](./tests/golden/02_cat.yml)

---


## Input Schedule

Provided via:

```text
input_schedule.json
```

Example:

```json
{
    "events": [
        {
            "tick": 2,
            "token": "H"
        },
        {
            "tick": 12,
            "token": "E"
        },
        {
            "tick": 20,
            "token": "Y"
        }
    ]
}
```

---

# Pipeline

```text
+--------+     +--------+     +---------+
| Fetch  | --> | Decode | --> | Execute |
+--------+     +--------+     +---------+
```

## Fetch

* reads the instruction from memory;
* loads the instruction into `IR`;
* updates the instruction address.

## Decode

* interprets the opcode;
* determines instruction length;
* resolves addressing modes;
* prepares operands.

## Execute

* performs ALU operations;
* performs memory access;
* resolves branches;
* writes results;
* executes I/O operations;
* handles relevant processor-control operations.

---

# Example Toolchain

## Compile ALG

```bash
make compile-alg program.alg
```

Produces:

```text
program.asm
program.bin
program.lst
```

## Run ALG

```bash
make run-alg program.alg isr.alg
```

## Run Assembly

```bash
make run-asm program.asm isr.asm
```

## Run Binary

```bash
make run-bin program.bin isr.bin
```

## Verbose Simulation

```bash
make run-alg program.alg isr.alg mode=verbose
```

## Silent Simulation

```bash
make run-alg program.alg isr.alg mode=silent
```

## Direct Python Usage

```bash
python -m src.main compile-alg program.alg

python -m src.main run-alg program.alg isr.alg

python -m src.main run-asm program.asm isr.asm

python -m src.main run-bin program.bin isr.bin
```

---

# Documentation

Detailed documentation is available in:

* [`docs/alg.md`](./docs/alg.md) — ALG syntax and semantics;
* [`docs/isa.md`](./docs/isa.md) — PipeCore processor and instruction set;
* [`docs/encoding.md`](./docs/encoding.md) — binary instruction encoding;
* [`docs/memory.md`](./docs/memory.md) — memory organization;
* [`docs/registers.md`](./docs/registers.md) — register architecture.

---
