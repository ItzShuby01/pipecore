# PipeCore Binary Encoding

## Instruction Encoding

PipeCore uses **variable-length instructions**.

Instruction size depends on:

- operation code (opcode)
- number of operands
- addressing mode

Supported sizes:

- 1 word
- 2 words
- 3 words
- 4 words

## Binary Instruction Encoding

Every instruction starts with a fixed 32-bit header, followed by zero or more operand words.

Layout:

`[ Header (32 bits) ] [ Operand 1 ] [ Operand 2 ] [ Operand 3 ]`

### Header Format

| Bits | Field |
|------|------|
| 31–24 | Opcode |
| 23–20 | Operand Count |
| 19–16 | Addressing Mode 1 |
| 15–12 | Addressing Mode 2 |
| 11–8 | Addressing Mode 3 |
| 7–0 | Flags |

### Example Encodings

- `HALT` : 1 word

- `INC R1` : 2 words
- `MOV #5, R1` : 3 words
- `ADD [100], [200], R3` : 4 words 


## Opcode Encoding Table

<table>
  <thead>
    <tr>
      <th>Category</th>
      <th>Instruction</th>
      <th>Opcode (hex)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2"><b>System</b><br>(0x00–0x0F)</td>
      <td>NOP</td>
      <td>0x00</td>
    </tr>
    <tr>
      <td>HALT</td>
      <td>0x01</td>
    </tr>
    <tr>
      <td rowspan="5"><b>Data Movement</b><br>(0x10–0x1F)</td>
      <td>MOV</td>
      <td>0x10</td>
    </tr>
    <tr>
      <td>LOAD</td>
      <td>0x11</td>
    </tr>
    <tr>
      <td>STORE</td>
      <td>0x12</td>
    </tr>
    <tr>
      <td>PUSH</td>
      <td>0x13</td>
    </tr>
    <tr>
      <td>POP</td>
      <td>0x14</td>
    </tr>
    <tr>
      <td rowspan="7"><b>Arithmetic</b><br>(0x20–0x2F)</td>
      <td>ADD</td>
      <td>0x20</td>
    </tr>
    <tr>
      <td>SUB</td>
      <td>0x21</td>
    </tr>
    <tr>
      <td>MUL</td>
      <td>0x22</td>
    </tr>
    <tr>
      <td>DIV</td>
      <td>0x23</td>
    </tr>
    <tr>
      <td>MOD</td>
      <td>0x24</td>
    </tr>
    <tr>
      <td>INC</td>
      <td>0x25</td>
    </tr>
    <tr>
      <td>DEC</td>
      <td>0x26</td>
    </tr>
    <tr>
      <td rowspan="9"><b>Control Flow</b><br>(0x30–0x4F)</td>
      <td>CMP</td>
      <td>0x30</td>
    </tr>
    <tr>
      <td>JMP</td>
      <td>0x31</td>
    </tr>
    <tr>
      <td>JZ</td>
      <td>0x32</td>
    </tr>
    <tr>
      <td>JNZ</td>
      <td>0x33</td>
    </tr>
    <tr>
      <td>JLT</td>
      <td>0x34</td>
    </tr>
    <tr>
      <td>JGT</td>
      <td>0x35</td>
    </tr>
    <tr>
      <td>CALL</td>
      <td>0x40</td>
    </tr>
    <tr>
      <td>RET</td>
      <td>0x41</td>
    </tr>
    <tr>
      <td>IRET</td>
      <td>0x42</td>
    </tr>
    <tr>
      <td rowspan="2"><b>I/O</b><br>(0x50–0x5F)</td>
      <td>IN</td>
      <td>0x50</td>
    </tr>
    <tr>
      <td>OUT</td>
      <td>0x51</td>
    </tr>
  </tbody>
</table>


## Addressing Mode Encoding Table

| Mode | Value |
|------|------|
| Immediate | 0x0 |
| Register | 0x1 |
| Direct Memory | 0x2 |
| Register Indirect | 0x3 |
| Indexed | 0x4 |



## Register Encoding Table

| Register | Code |
|---------|------|
| R0 | 0x0 |
| R1 | 0x1 |
| R2 | 0x2 |
| R3 | 0x3 |
| IP | 0x4 |
| SP | 0x5 |
| IR | 0x6 |
| FLAGS | 0x7 |



## Port Encoding Table

| Port | Code |
|------|------|
| P0 (Input) | 0x0 |
| P1 (Output) | 0x1 |
| P2 (Status) | 0x2 |


## Flag Encoding Table

| Flag | Bit |
|------|----|
| Z | 0 |
| N | 1 |
| C | 2 |
| O | 3 |
| I | 4 |