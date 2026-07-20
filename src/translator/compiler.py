from __future__ import annotations
from dataclasses import dataclass
from src.translator.alg import (
    Program, VarDecl, ProcedureDecl, InterruptDecl, AssignStmt, IfStmt,
    WhileStmt, ReturnStmt, OutputStmt, InputStmt, BinOpExpr, IntLiteral,
    CharLiteral, StringLiteral, BoolLiteral, VariableExpr, CallExpr, Expr, Stmt
)


@dataclass
class SymbolRecord:
    name: str
    type_name: str
    is_global: bool
    address: int | None = None
    stack_offset: int | None = None


class SymbolTable:
    def __init__(self, parent: SymbolTable | None = None):
        self.symbols: dict[str, SymbolRecord] = {}
        self.parent = parent

    def lookup(self, name: str) -> SymbolRecord | None:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def define(self, record: SymbolRecord) -> None:
        self.symbols[record.name] = record


class SemanticAnalyzer:
    def __init__(self):
        self.global_table = SymbolTable()
        self.current_table = self.global_table
        self.static_alloc_ptr = 0x1000
        self.string_literals: list[tuple[int, str]] = []
        self.current_procedure: ProcedureDecl | None = None
        self.in_interrupt_context = False

    def allocate_static(self, size_words: int) -> int:
        addr = self.static_alloc_ptr
        self.static_alloc_ptr += size_words * 4
        if self.static_alloc_ptr > 0x7FFF:
            raise MemoryError(
                "Static memory allocation overflowed 0x7FFF segment bounds.")
        return addr

    def analyze(self, program: Program) -> None:
        for decl in program.decls:
            if isinstance(decl, ProcedureDecl):
                self.global_table.define(SymbolRecord(
                    decl.name, "procedure", is_global=True))

        for decl in program.decls:
            if isinstance(decl, VarDecl):
                self.analyze_global_var(decl)
            elif isinstance(decl, ProcedureDecl):
                self.analyze_procedure(decl)
            elif isinstance(decl, InterruptDecl):
                self.analyze_interrupt(decl)

    def analyze_global_var(self, decl: VarDecl) -> None:
        if self.global_table.lookup(decl.name):
            raise SyntaxError(
                f"Line {decl.line}: Duplicate global structural variable definition '{decl.name}'")

        size = 1
        if decl.var_type.name == "string":
            size = 32
            if decl.init_expr and isinstance(decl.init_expr, StringLiteral):
                size = 1 + len(decl.init_expr.value)

        addr = self.allocate_static(size)
        record = SymbolRecord(decl.name, decl.var_type.name,
                              is_global=True, address=addr)
        self.global_table.define(record)

        if decl.init_expr:
            init_type = self.check_expr_type(decl.init_expr)
            if init_type != decl.var_type.name:
                raise SyntaxError(
                    f"Line {decl.line}: Type mismatch in global initialization. Expected '{decl.var_type.name}', got '{init_type}'")

    def analyze_procedure(self, decl: ProcedureDecl) -> None:
        self.current_procedure = decl
        local_table = SymbolTable(parent=self.global_table)
        self.current_table = local_table

        offset = 12
        for param in decl.params:
            record = SymbolRecord(
                param.name, param.param_type.name, is_global=False, stack_offset=offset)
            local_table.define(record)
            offset += 4

        self.local_var_offset = -4
        for stmt in decl.body:
            self.analyze_stmt(stmt)

        self.current_table = self.global_table
        self.current_procedure = None

    def analyze_interrupt(self, decl: InterruptDecl) -> None:
        self.in_interrupt_context = True
        local_table = SymbolTable(parent=self.global_table)
        self.current_table = local_table
        self.local_var_offset = -4
        for stmt in decl.body:
            self.analyze_stmt(stmt)
        self.current_table = self.global_table
        self.in_interrupt_context = False

    def analyze_stmt(self, stmt: VarDecl | AssignStmt | IfStmt | WhileStmt | ReturnStmt | OutputStmt | InputStmt) -> None:
        if isinstance(stmt, VarDecl):
            if stmt.var_type.name == "string":
                raise SyntaxError(
                    f"Line {stmt.line}: String stack allocations not permitted locally. Use global variables.")

            record = SymbolRecord(stmt.name, stmt.var_type.name,
                                  is_global=False, stack_offset=self.local_var_offset)
            self.current_table.define(record)
            self.local_var_offset -= 4

            if stmt.init_expr:
                init_type = self.check_expr_type(stmt.init_expr)
                if init_type != stmt.var_type.name:
                    raise SyntaxError(
                        f"Line {stmt.line}: Type mismatch initializing local variable. Got '{init_type}'")

        elif isinstance(stmt, AssignStmt):
            sym = self.current_table.lookup(stmt.name)
            if not sym:
                raise SyntaxError(
                    f"Line {stmt.line}: Unresolved variable modifier execution target '{stmt.name}'")
            expr_type = self.check_expr_type(stmt.expr)
            if sym.type_name != expr_type:
                raise SyntaxError(
                    f"Line {stmt.line}: Cannot assign expression of type '{expr_type}' to target variable of type '{sym.type_name}'")

        elif isinstance(stmt, InputStmt):
            if not self.in_interrupt_context:
                raise SyntaxError(
                    f"Line {stmt.line}: semantic error: input() is only valid inside the input interrupt handler.")
            sym = self.current_table.lookup(stmt.name)
            if not sym:
                raise SyntaxError(
                    f"Line {stmt.line}: Unresolved reference target variable for input stream execution logic '{stmt.name}'")
            if sym.type_name not in {"int", "char"}:
                raise SyntaxError(
                    f"Line {stmt.line}: System hardware target container target must resolve to int or char scalar variants.")

        elif isinstance(stmt, OutputStmt):
            self.check_expr_type(stmt.expr)

        elif isinstance(stmt, IfStmt):
            if self.check_expr_type(stmt.condition) != "boolean":
                raise SyntaxError(
                    f"Line {stmt.line}: Statement evaluation context condition must be boolean.")
            for s in stmt.then_branch:
                self.analyze_stmt(s)
            for s in stmt.else_branch:
                self.analyze_stmt(s)

        elif isinstance(stmt, WhileStmt):
            if self.check_expr_type(stmt.condition) != "boolean":
                raise SyntaxError(
                    f"Line {stmt.line}: While structural validation condition expression context must evaluate to boolean.")
            for s in stmt.body:
                self.analyze_stmt(s)

        elif isinstance(stmt, ReturnStmt):
            actual_type = self.check_expr_type(
                stmt.expr) if stmt.expr else None
            expected_type = self.current_procedure.return_type.name if (
                self.current_procedure and self.current_procedure.return_type) else None
            if actual_type != expected_type:
                raise SyntaxError(
                    f"Line {stmt.line}: Procedure return expression type mismatch. Expected '{expected_type}', got '{actual_type}'")

    def check_expr_type(self, expr: Expr) -> str:
        if isinstance(expr, IntLiteral):
            return "int"
        elif isinstance(expr, CharLiteral):
            return "char"
        elif isinstance(expr, BoolLiteral):
            return "boolean"
        elif isinstance(expr, StringLiteral):
            addr = self.allocate_static(1 + len(expr.value))
            self.string_literals.append((addr, expr.value))
            return "string"
        elif isinstance(expr, VariableExpr):
            sym = self.current_table.lookup(expr.name)
            if not sym:
                raise SyntaxError(
                    f"Line {expr.line}: Unresolved runtime variable invocation reference lookup '{expr.name}'")
            return sym.type_name
        elif isinstance(expr, BinOpExpr):
            lt = self.check_expr_type(expr.left)
            rt = self.check_expr_type(expr.right)
            if expr.op in {"+", "-", "*", "/", "%"}:
                if lt != "int" or rt != "int":
                    raise SyntaxError(
                        f"Line {expr.line}: Arithmetic parameters require structural integer operations.")
                return "int"
            else:
                if lt != rt:
                    raise SyntaxError(
                        f"Line {expr.line}: Comparators demand uniform operational type validation sets.")
                return "boolean"
        elif isinstance(expr, CallExpr):
            if expr.name == "input":
                if not self.in_interrupt_context:
                    raise SyntaxError(
                        f"Line {expr.line}: semantic error: input() is only valid inside the input interrupt handler.")
                return "int"
            if not self.global_table.lookup(expr.name):
                raise SyntaxError(
                    f"Line {expr.line}: Unresolved functional routing target context location '{expr.name}'")
            return "int"
        return "void"


class CodeGenerator:
    def __init__(self, analyzer: SemanticAnalyzer):
        self.analyzer = analyzer
        self.instructions: list[str] = []
        self.label_counter = 0

    def generate_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"_{prefix}_{self.label_counter}"

    def emit(self, instruction: str) -> None:
        self.instructions.append(instruction)

    def generate(self, program: Program) -> str:
        has_interrupt = any(isinstance(d, InterruptDecl)
                            for d in program.decls)

        has_procedures = any(isinstance(d, ProcedureDecl)
                             for d in program.decls)
        has_global_vars = any(isinstance(d, VarDecl) for d in program.decls)
        has_main_stmts = any(isinstance(d, Stmt) for d in program.decls)
        is_standalone_isr = has_interrupt and not (
            has_procedures or has_global_vars or has_main_stmts)

        if is_standalone_isr:
            for decl in program.decls:
                if isinstance(decl, InterruptDecl):
                    self.generate_interrupt(decl)
            return "\n".join(self.instructions)

        if has_interrupt:
            self.emit("MOV _isr_input, R0")
            self.emit("STORE R0, [0x0000]")

        self.emit("JMP _start")

        for decl in program.decls:
            if isinstance(decl, ProcedureDecl):
                self.generate_procedure(decl)
            elif isinstance(decl, InterruptDecl):
                self.generate_interrupt(decl)

        self.emit("_start:")

        for addr, val in self.analyzer.string_literals:
            self.emit(f"MOV {len(val)}, R0")
            self.emit(f"STORE R0, [{addr}]")
            for i, ch in enumerate(val):
                self.emit(f"MOV {ord(ch)}, R0")
                self.emit(f"STORE R0, [{addr + 4 + (i * 4)}]")

        for decl in program.decls:
            if isinstance(decl, VarDecl) and decl.init_expr:
                self.generate_expr(decl.init_expr, "R0")
                sym = self.analyzer.global_table.lookup(decl.name)
                self.emit(f"STORE R0, [{sym.address}]")

        main_proc = self.analyzer.global_table.lookup("main")
        if main_proc:
            self.emit("CALL main")

        self.emit("HALT")
        return "\n".join(self.instructions)

    def generate_procedure(self, decl: ProcedureDecl) -> None:
        self.emit(f"{decl.name}:")
        self.emit("PUSH R2")
        self.emit("MOV SP, R2")

        local_records = [r for r in self.analyzer.global_table.symbols.values(
        ) if r.stack_offset and r.stack_offset < 0]
        if local_records:
            space = len(local_records) * 4
            self.emit(f"SUB SP, {space}, SP")

        for stmt in decl.body:
            self.generate_stmt(stmt)

        self.emit("MOV R2, SP")
        self.pop_frame_and_ret()

    def pop_frame_and_ret(self) -> None:
        self.emit("POP R2")
        self.emit("RET")

    def generate_interrupt(self, decl: InterruptDecl) -> None:
        self.emit(f"_isr_{decl.name}:")
        for stmt in decl.body:
            self.generate_stmt(stmt)
        self.emit("IRET")

    def generate_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            if stmt.init_expr:
                self.generate_expr(stmt.init_expr, "R1")
                sym = self.analyzer.current_table.lookup(stmt.name)
                self.emit(f"STORE R1, [R2 + {sym.stack_offset}]")

        elif isinstance(stmt, AssignStmt):
            self.generate_expr(stmt.expr, "R1")
            sym = self.analyzer.current_table.lookup(stmt.name)
            if sym.is_global:
                self.emit(f"STORE R1, [{sym.address}]")
            else:
                self.emit(f"STORE R1, [R2 + {sym.stack_offset}]")

        elif isinstance(stmt, InputStmt):
            self.emit("IN P0, R1")
            sym = self.analyzer.current_table.lookup(stmt.name)
            if sym.is_global:
                self.emit(f"STORE R1, [{sym.address}]")
            else:
                self.emit(f"STORE R1, [R2 + {sym.stack_offset}]")

        elif isinstance(stmt, OutputStmt):
            if isinstance(stmt.expr, CallExpr) and stmt.expr.name == "input":
                self.emit("IN P0, R1")
                self.emit("OUT P1, R1")
            else:
                self.generate_expr(stmt.expr, "R1")
                self.emit("OUT P1, R1")

        elif isinstance(stmt, ReturnStmt):
            if stmt.expr:
                self.generate_expr(stmt.expr, "R1")
            self.emit("MOV R2, SP")
            self.pop_frame_and_ret()

        elif isinstance(stmt, IfStmt):
            label_false = self.generate_label("if_false")
            label_end = self.generate_label("if_end")

            self.generate_expr(stmt.condition, "R1")
            self.emit("CMP R1, 0")
            self.emit(f"JZ {label_false}")

            for s in stmt.then_branch:
                self.generate_stmt(s)
            self.emit(f"JMP {label_end}")

            self.emit(f"{label_false}:")
            for s in stmt.else_branch:
                self.generate_stmt(s)

            self.emit(f"{label_end}:")

        elif isinstance(stmt, WhileStmt):
            label_start = self.generate_label("while_start")
            label_end = self.generate_label("while_end")

            self.emit(f"{label_start}:")
            self.generate_expr(stmt.condition, "R1")
            self.emit("CMP R1, 0")
            self.emit(f"JZ {label_end}")

            for s in stmt.body:
                self.generate_stmt(s)
            self.emit(f"JMP {label_start}")
            self.emit(f"{label_end}:")

    def generate_expr(self, expr: Expr, reg_dst: str) -> None:
        if isinstance(expr, IntLiteral):
            self.emit(f"MOV {expr.value}, {reg_dst}")
        elif isinstance(expr, CharLiteral):
            self.emit(f"MOV {ord(expr.value)}, {reg_dst}")
        elif isinstance(expr, BoolLiteral):
            val = 1 if expr.value else 0
            self.emit(f"MOV {val}, {reg_dst}")
        elif isinstance(expr, StringLiteral):
            found_addr = None
            for addr, val in self.analyzer.string_literals:
                if val == expr.value:
                    found_addr = addr
                    break
            self.emit(f"MOV {found_addr}, {reg_dst}")
        elif isinstance(expr, VariableExpr):
            sym = self.analyzer.current_table.lookup(expr.name)
            if sym.is_global:
                self.emit(f"LOAD [{sym.address}], {reg_dst}")
            else:
                self.emit(f"LOAD [R2 + {sym.stack_offset}], {reg_dst}")
        elif isinstance(expr, CallExpr) and expr.name == "input":
            self.emit(f"IN P0, {reg_dst}")
        elif isinstance(expr, BinOpExpr):
            self.generate_expr(expr.left, "R0")
            self.emit("PUSH R0")
            self.generate_expr(expr.right, "R1")
            self.emit("POP R0")

            if expr.op == "+":
                self.emit(f"ADD R0, R1, {reg_dst}")
            elif expr.op == "-":
                self.emit(f"SUB R0, R1, {reg_dst}")
            elif expr.op == "*":
                self.emit(f"MUL R0, R1, {reg_dst}")
            elif expr.op == "/":
                self.emit(f"DIV R0, R1, {reg_dst}")
            elif expr.op == "%":
                self.emit(f"MOD R0, R1, {reg_dst}")
            elif expr.op in {"==", "!=", "<", "<=", ">", ">="}:
                self.emit("CMP R0, R1")
                lbl_true = self.generate_label("op_true")
                lbl_end = self.generate_label("op_end")

                if expr.op == "==":
                    self.emit(f"JZ {lbl_true}")
                elif expr.op == "!=":
                    self.emit(f"JNZ {lbl_true}")
                elif expr.op == "<":
                    self.emit(f"JLT {lbl_true}")
                elif expr.op == ">":
                    self.emit(f"JGT {lbl_true}")
                elif expr.op == "<=":
                    self.emit(f"JLT {lbl_true}")
                    self.emit(f"JZ {lbl_true}")
                elif expr.op == ">=":
                    self.emit(f"JGT {lbl_true}")
                    self.emit(f"JZ {lbl_true}")

                self.emit(f"MOV 0, {reg_dst}")
                self.emit(f"JMP {lbl_end}")
                self.emit(f"{lbl_true}:")
                self.emit(f"MOV 1, {reg_dst}")
                self.emit(f"{lbl_end}:")
