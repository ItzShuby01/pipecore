from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class ASTNode:
    line: int


@dataclass
class TypeNode(ASTNode):
    name: str  # 'int', 'char', 'string', 'boolean'


@dataclass
class Expr(ASTNode):
    pass


@dataclass
class IntLiteral(Expr):
    value: int


@dataclass
class CharLiteral(Expr):
    value: str


@dataclass
class StringLiteral(Expr):
    value: str


@dataclass
class BoolLiteral(Expr):
    value: bool


@dataclass
class VariableExpr(Expr):
    name: str


@dataclass
class BinOpExpr(Expr):
    left: Expr
    op: str  # '+', '-', '*', '/', '%', '==', '!=', '<', '<=', '>', '>='
    right: Expr


@dataclass
class CallExpr(Expr):
    name: str
    args: list[Expr]


@dataclass
class Stmt(ASTNode):
    pass


@dataclass
class VarDecl(Stmt):
    name: str
    var_type: TypeNode
    init_expr: Expr | None = None


@dataclass
class AssignStmt(Stmt):
    name: str
    expr: Expr


@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: list[Stmt]
    else_branch: list[Stmt] = field(default_factory=list)


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: list[Stmt]


@dataclass
class ReturnStmt(Stmt):
    expr: Expr | None = None


@dataclass
class InputStmt(Stmt):
    name: str


@dataclass
class OutputStmt(Stmt):
    expr: Expr


@dataclass
class Param(ASTNode):
    name: str
    param_type: TypeNode


@dataclass
class ProcedureDecl(ASTNode):
    name: str
    params: list[Param]
    return_type: TypeNode | None
    body: list[Stmt]


@dataclass
class InterruptDecl(ASTNode):
    name: str
    body: list[Stmt]


@dataclass
class Program(ASTNode):
    decls: list[ASTNode]


@dataclass
class Token:
    type: str
    value: str
    line: int


class Lexer:
    KEYWORDS = {
        "var", "procedure", "interrupt", "input", "output",
        "if", "else", "while", "return", "true", "false",
        "int", "char", "string", "boolean"
    }

    TOKEN_SPECIFICATION = [
        ("ASSIGN",     r":="),
        ("EQ",         r"=="),
        ("NEQ",        r"!="),
        ("LEQ",         r"<="),
        ("GEQ",         r">="),
        ("LT",         r"<"),
        ("GT",         r">"),
        ("PLUS",       r"\+"),
        ("MINUS",      r"-"),
        ("MUL",        r"\*"),
        ("DIV",        r"/"),
        ("MOD",        r"%"),
        ("LPAREN",     r"\("),
        ("RPAREN",     r"\)"),
        ("LBRACE",     r"\{"),
        ("RBRACE",     r"\}"),
        ("COMMA",      r","),
        ("SEMI",       r";"),
        ("COLON",      r":"),
        ("STRING",     r'"[^"\n]*"'),
        ("CHAR",       r"'[^'\n]'"),
        ("INT",        r"\d+"),
        ("ID",         r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("NEWLINE",    r"\n"),
        ("SKIP",       r"[ \t\r]+"),
        ("MISMATCH",   r"."),
    ]

    @classmethod
    def tokenize(cls, source_code: str) -> list[Token]:
        tokens: list[Token] = []
        line_number = 1

        tok_regex = "|".join(
            f"(?P<{name}>{pattern})" for name, pattern in cls.TOKEN_SPECIFICATION)

        for mo in re.finditer(tok_regex, source_code):
            kind = mo.lastgroup
            assert kind is not None
            value = mo.group(kind)

            if kind == "NEWLINE":
                line_number += 1
            elif kind == "SKIP":
                continue
            elif kind == "MISMATCH":
                raise SyntaxError(
                    f"Line {line_number}: Unexpected character sequence structure '{value}'")
            else:
                if kind == "ID" and value in cls.KEYWORDS:
                    kind = value.upper()
                tokens.append(Token(kind, value, line_number))

        return tokens


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token("EOF", "", -1)

    def consume(self, expected_type: str) -> Token:
        tok = self.current_token()
        if tok.type != expected_type:
            raise SyntaxError(
                f"Line {tok.line}: Expected token type '{expected_type}', got '{tok.type}' ('{tok.value}')")
        self.pos += 1
        return tok

    def match(self, *types: str) -> bool:
        tok = self.current_token()
        if tok.type in types:
            self.pos += 1
            return True
        return False

    def parse_program(self) -> Program:
        decls: list[ASTNode] = []
        first_line = self.current_token().line
        while self.current_token().type != "EOF":
            tok = self.current_token()
            if tok.type == "VAR":
                decls.append(self.parse_var_decl())
            elif tok.type == "PROCEDURE":
                decls.append(self.parse_procedure_decl())
            elif tok.type == "INTERRUPT":
                decls.append(self.parse_interrupt_decl())
            else:
                decls.append(self.parse_stmt())
        return Program(line=first_line, decls=decls)

    def parse_var_decl(self) -> VarDecl:
        start_tok = self.consume("VAR")
        name = self.consume("ID").value

        var_type = None
        if self.match("COLON"):
            type_tok = self.current_token()
            if type_tok.type not in {"INT", "CHAR", "STRING", "BOOLEAN"}:
                raise SyntaxError(
                    f"Line {type_tok.line}: Invalid type declaration '{type_tok.value}'")
            self.pos += 1
            var_type = TypeNode(line=type_tok.line,
                                name=type_tok.value.lower())
        else:
            var_type = TypeNode(line=start_tok.line, name="int")

        init_expr = None
        if self.match("ASSIGN"):
            init_expr = self.parse_expr()

        self.consume("SEMI")
        return VarDecl(line=start_tok.line, name=name, var_type=var_type, init_expr=init_expr)

    def parse_procedure_decl(self) -> ProcedureDecl:
        start_tok = self.consume("PROCEDURE")
        name = self.consume("ID").value
        self.consume("LPAREN")
        params = []
        if self.current_token().type != "RPAREN":
            while True:
                p_name = self.consume("ID").value
                self.consume("COLON")
                t_tok = self.current_token()
                self.pos += 1
                p_type = TypeNode(line=t_tok.line, name=t_tok.value.lower())
                params.append(
                    Param(line=t_tok.line, name=p_name, param_type=p_type))
                if not self.match("COMMA"):
                    break
        self.consume("RPAREN")

        ret_type = None
        if self.match("COLON"):
            t_tok = self.current_token()
            self.pos += 1
            ret_type = TypeNode(line=t_tok.line, name=t_tok.value.lower())

        self.consume("LBRACE")
        body = []
        while self.current_token().type != "RBRACE":
            body.append(self.parse_stmt())
        self.consume("RBRACE")

        return ProcedureDecl(line=start_tok.line, name=name, params=params, return_type=ret_type, body=body)

    def parse_interrupt_decl(self) -> InterruptDecl:
        start_tok = self.consume("INTERRUPT")
        name = self.consume("INPUT").value
        self.consume("LBRACE")
        body = []
        while self.current_token().type != "RBRACE":
            body.append(self.parse_stmt())
        self.consume("RBRACE")
        return InterruptDecl(line=start_tok.line, name=name, body=body)

    def parse_stmt(self) -> Stmt:
        tok = self.current_token()
        if tok.type == "VAR":
            return self.parse_var_decl()
        elif tok.type == "IF":
            self.pos += 1
            self.consume("LPAREN")
            cond = self.parse_expr()
            self.consume("RPAREN")

            then_branch = self.parse_block()
            else_branch = []
            if self.match("ELSE"):
                else_branch = self.parse_block()
            return IfStmt(line=tok.line, condition=cond, then_branch=then_branch, else_branch=else_branch)
        elif tok.type == "WHILE":
            self.pos += 1
            self.consume("LPAREN")
            cond = self.parse_expr()
            self.consume("RPAREN")
            body = self.parse_block()
            return WhileStmt(line=tok.line, condition=cond, body=body)
        elif tok.type == "RETURN":
            self.pos += 1
            expr = None
            if self.current_token().type != "SEMI":
                expr = self.parse_expr()
            self.consume("SEMI")
            return ReturnStmt(line=tok.line, expr=expr)
        elif tok.type == "LBRACE":
            line = tok.line
            self.parse_block()
            return ReturnStmt(line=line, expr=None)
        elif tok.type == "ID" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == "ASSIGN":
            name = tok.value
            self.pos += 2

            if self.current_token().type == "INPUT":
                self.pos += 1
                self.consume("LPAREN")
                self.consume("RPAREN")
                self.consume("SEMI")
                return InputStmt(line=tok.line, name=name)

            expr = self.parse_expr()
            self.consume("SEMI")
            return AssignStmt(line=tok.line, name=name, expr=expr)
        else:
            expr = self.parse_expr()
            self.consume("SEMI")
            if isinstance(expr, CallExpr) and expr.name == "output":
                if not expr.args:
                    raise SyntaxError(
                        f"Line {tok.line}: output() requires an argument.")
                return OutputStmt(line=tok.line, expr=expr.args[0])
            return ReturnStmt(line=tok.line, expr=expr)

    def parse_block(self) -> list[Stmt]:
        self.consume("LBRACE")
        stmts = []
        while self.current_token().type != "RBRACE" and self.current_token().type != "EOF":
            stmts.append(self.parse_stmt())
        self.consume("RBRACE")
        return stmts

    def parse_expr(self) -> Expr:
        return self.parse_comparison()

    def parse_comparison(self) -> Expr:
        expr = self.parse_additive()
        while self.current_token().type in {"EQ", "NEQ", "LT", "LEQ", "GT", "GEQ"}:
            op = self.current_token().value
            self.pos += 1
            right = self.parse_additive()
            expr = BinOpExpr(line=expr.line, left=expr, op=op, right=right)
        return expr

    def parse_additive(self) -> Expr:
        expr = self.parse_multiplicative()
        while self.current_token().type in {"PLUS", "MINUS"}:
            op = self.current_token().value
            self.pos += 1
            right = self.parse_multiplicative()
            expr = BinOpExpr(line=expr.line, left=expr, op=op, right=right)
        return expr

    def parse_multiplicative(self) -> Expr:
        expr = self.parse_unary()
        while self.current_token().type in {"MUL", "DIV", "MOD"}:
            op = self.current_token().value
            self.pos += 1
            right = self.parse_unary()
            expr = BinOpExpr(line=expr.line, left=expr, op=op, right=right)
        return expr

    def parse_unary(self) -> Expr:
        if self.match("MINUS"):
            tok = self.tokens[self.pos - 1]
            operand = self.parse_unary()
            return BinOpExpr(line=tok.line, left=IntLiteral(line=tok.line, value=0), op="-", right=operand)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        tok = self.current_token()
        if self.match("INT"):
            return IntLiteral(line=tok.line, value=int(tok.value))
        elif self.match("CHAR"):
            return CharLiteral(line=tok.line, value=tok.value[1:-1])
        elif self.match("STRING"):
            return StringLiteral(line=tok.line, value=tok.value[1:-1])
        elif self.match("TRUE"):
            return BoolLiteral(line=tok.line, value=True)
        elif self.match("FALSE"):
            return BoolLiteral(line=tok.line, value=False)
        elif self.match("INPUT"):
            self.consume("LPAREN")
            self.consume("RPAREN")
            return CallExpr(line=tok.line, name="input", args=[])
        elif tok.type == "OUTPUT":
            self.pos += 1
            self.consume("LPAREN")
            expr = self.parse_expr()
            self.consume("RPAREN")
            return CallExpr(line=tok.line, name="output", args=[expr])
        elif tok.type == "ID":
            name = tok.value
            self.pos += 1
            if self.match("LPAREN"):
                args = []
                if self.current_token().type != "RPAREN":
                    while True:
                        args.append(self.parse_expr())
                        if not self.match("COMMA"):
                            break
                self.consume("RPAREN")
                return CallExpr(line=tok.line, name=name, args=args)
            return VariableExpr(line=tok.line, name=name)
        elif self.match("LPAREN"):
            expr = self.parse_expr()
            self.consume("RPAREN")
            return expr
        else:
            raise SyntaxError(
                f"Line {tok.line}: Expected target secondary expression token tier, got '{tok.value}'")
