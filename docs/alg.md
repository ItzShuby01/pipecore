## Programming Language

### General Characteristics

 `ALG` language supports:

* integer arithmetic;
* variables and assignment;
* conditional statements;
* `while` loops;
* procedures and procedure calls;
* character and string literals;
* port-based input and output;
* interrupt handlers.

---

### Syntax (BNF)

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


<interrupt-declaration> ::= "interrupt" "input"
                            "{"
                                { <declaration> | <statement> }
                            "}"


<parameter-list> ::= <parameter> { "," <parameter> }

<parameter> ::= <identifier> [ ":" <type> ]


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


<input-expression> ::= "input" "(" ")"

<output-expression> ::= "output" "(" <expression> ")"


<type> ::= "int"
         | "char"
         | "string"


<literal> ::= <integer-literal>
            | <character-literal>
            | <string-literal>


<integer-literal> ::= <digit> { <digit> }

<character-literal> ::= "'" <character> "'"

<string-literal> ::= "\"" { <string-character> } "\""


<identifier> ::= <letter> { <letter> | <digit> | "_" }


<digit> ::= "0" | "1" | "2" | "3" | "4"
          | "5" | "6" | "7" | "8" | "9"


<letter> ::= "a" | "b" | ... | "z"
           | "A" | "B" | ... | "Z"
```

---

### Semantics

#### Evaluation Strategy

- Expressions are evaluated eagerly;
- Operands are evaluated from left to right;
- Arithmetic operators follow the standard precedence rules.;
- Only the selected branch of an `if` statement is executed;
- `while` evaluates its condition before every iteration;
- Procedure arguments are evaluated before the procedure is called;


Operator precedence **(highest to lowest):**

1. unary minus (`-x`)
2. multiplication, division, remainder (`*`, `/`, `%`)
3. addition and subtraction (`+`, `-`)
4. comparison operators (`==`, `!=`, `<`, `<=`, `>`, `>=`)

Also:
- Integer division is signed integer division.

* Comparison operations return a `boolean`.

---

#### Scope

`ALG` uses lexical (block) scope.

* Variable is visible from its declaration to the end of the block in which it is declared;
* Variables declared inside a block cannot be accessed outside that block;
* Procedure parameters and local variables are accessible only within the procedure;
* Declaration in an inner block may hide a variable with the same name from an outer scope/block;
* Global variables are visible throughout the program after declaration.

---

#### Data Types

| Type     | Purpose                                         |
| -------- | ----------------------------------------------- |
| `int`    | signed 32-bit integer                           |
| `char`   | one character represented by its character code |
| `string` | sequence of characters stored in `pstr` format  |

Variable's type is fixed after declaration. Assignments and operands in expressions must have compatible types.

---

#### Literals

| Literal   | Example      | Type     |
| --------- | ------------ | -------- |
| Integer   | `42`, `-10`  | `int`    |
| Character | `'A'`, `'!'` | `char`   |
| String    | `"HELLO"`    | `string` |

- Character literals are represented by their character codes.

- String literals are stored using the `pstr` representation. A string contains its length followed by its characters.

For example:

```text
"HELLO" → [5, 'H', 'E', 'L', 'L', 'O']
```

---

### Variables and Assignment

Variables are declared using `var`:

```text
var x: int;
var c: char;
var text: string;
```

Assignment is performed using `:=`:

```text
x := 10;
x := x + 5;
```

The right-hand side is evaluated first, after which the result is assigned to the variable.

---

### Conditional Statements

```text
if (condition) {
    statements
} else {
    statements
}
```

The condition is evaluated. If it is true, the first block is executed; otherwise, the `else` block is executed (if present).

---

### Loops

```text
while (condition) {
    statements
}
```

The condition is evaluated before every iteration. The loop terminates when the condition becomes `false`.

---

### Procedures

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

Procedure calls are translated into `CALL` and `RET` instructions. The return address is stored and returned from the stack.

---

### Input and Output

Input and output are performed through processor ports.

```text
input()
output(value)
```

`input()` reads a token from input port `P0`.

`output(value)` writes one character to output port `P1`. Each output operation appends one character to the simulator's output buffer.

The final contents of the output buffer are displayed after simulation.

---

### Interrupt Handler

The interrupt handler is declared as:

```text
interrupt input {
    statements
}
```

The handler reads the input using `input()` and may process or output it.


The interrupt handler is translated into an ISR that terminates with the `IRET` instruction.

---

### Input Schedule

Input schedule is part of the simulator environment, but is not part of the program source.

Example:

```json
{
    "events": [
        {
            "tick": 2,
            "token": "H"
        },
        {
            "tick": 3,
            "token": "I"
        },
        {
            "tick": 4,
            "token": "M"
        }
    ]
}
```

The schedule is not a queue implemented by the program. It is an external input source used by the simulator.

---

### Translation


```text
Source program (.alg)
    ↓
Parser
    ↓
Semantic analysis
    ↓
PipeCore assembly (.asm)
    ↓
Assembler
    ↓
Machine code and LST file (.bin and .lst)
```


The generated program can then be executed by the simulator.
