from abc import ABC, abstractmethod
from typing import Callable, Tuple, Optional, Union
from enum import Enum


class AstNode(ABC):
    def __init__(self, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__()
        self.row = row
        self.line = line
        for k, v in props.items():
            setattr(self, k, v)

    @property
    def children(self)->Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self)->str:
        pass

    @property
    def tree(self)->[str, ...]:
        try:
            res = [str(self)]
            children_temp = self.children
            for i, child in enumerate(children_temp):
                ch0, ch = '├', '│'
                if i == len(children_temp) - 1:
                    ch0, ch = '└', ' '
                res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
            return res
        except AttributeError:
            print(res, children_temp)

    def visit(self, func: Callable[['AstNode'], None])->None:
        func(self)
        map(func, self.children)

    def __getitem__(self, index):
        return self.children[index] if index < len(self.children) else None


class ExprNode(AstNode):
    pass


class LiteralNode(ExprNode):
    def __init__(self, literal: str,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.literal = literal
        self.value = eval(literal)

    def __str__(self)->str:
        return '{0} ({1})'.format(self.literal, type(self.value).__name__)


class IdentNode(ExprNode):
    def __init__(self, name: str,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = str(name)

    def __str__(self)->str:
        return str(self.name)


class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    GE = '>='
    LE = '<='
    NEQUALS = '<>'
    EQUALS = '=='
    GT = '>'
    LT = '<'
    BIT_AND = '&'
    BIT_OR = '|'
    LOGICAL_AND = '&&'
    LOGICAL_OR = '||'


class BinOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2

    def __str__(self)->str:
        return str(self.op.value)


class StmtNode(ExprNode):
    pass


class VarsDeclNode(StmtNode):
    def __init__(self, vars_type: StmtNode, *vars_list: Tuple[AstNode, ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.vars_type = vars_type
        self.vars_list = vars_list

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self.vars_type, (*self.vars_list)

    def __str__(self)->str:
        return 'var'


class CallNode(StmtNode):
    def __init__(self, func: IdentNode, *params: Tuple[ExprNode],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.func = func
        self.params = params

    @property
    def children(self) -> Tuple[IdentNode, ...]:
        return self.func, (*self.params)

    def __str__(self)->str:
        return 'call'


class AssignNode(StmtNode):
    def __init__(self, var: IdentNode, val: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.var = var
        self.val = val

    @property
    def children(self) -> Tuple[IdentNode, ExprNode]:
        return self.var, self.val

    def __str__(self)->str:
        return '='


class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    @property
    def children(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.cond, self.then_stmt) + ((self.else_stmt, ) if self.else_stmt else tuple())

    def __str__(self)->str:
        return 'if'


class ForNode(StmtNode):
    def __init__(self, init: Union[StmtNode, None], cond: Union[ExprNode, StmtNode, None],
                 step: Union[StmtNode, None], body: Union[StmtNode, None] = None,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.init = init if init else _empty
        self.cond = cond if cond else _empty
        self.step = step if step else _empty
        self.body = body if body else _empty

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return self.init, self.cond, self.step, self.body

    def __str__(self)->str:
        return 'for'


class StmtListNode(StmtNode):
    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.exprs = exprs

    @property
    def children(self) -> Tuple[StmtNode, ...]:
        return self.exprs

    def __str__(self)->str:
        return '...'


class WhileNode(StmtNode):
    def __init__(self, cond: Union[ExprNode, StmtNode], body: Union[StmtNode, None],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond if cond else _empty
        self.body = body if body else _empty

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return self.cond, self.body

    def __str__(self) -> str:
        return 'while'


class DoWhileNode(StmtNode):
    def __init__(self, body: Union[StmtNode, None], cond: Union[ExprNode, StmtNode],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond if cond else _empty
        self.body = body if body else _empty

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return self.cond, self.body

    def __str__(self) -> str:
        return 'do_while'


class ArrayNode(StmtNode):
    def __init__(self, name: IdentNode, arr_type: IdentNode, length: LiteralNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.type = arr_type
        self.type.name += '[{0}]'.format(length.value)

    @property
    def children(self):
        return self.name, self.type

    def __str__(self) -> str:
        return '='


class ExprListNode(AstNode):
    def __init__(self, *contained,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.contained = contained

    @property
    def length(self):
        return len(self.contained)

    @property
    def children(self):
        return self.contained

    def __str__(self) -> str:
        return 'values'


class ValArrayNode(StmtNode):
    def __init__(self, name: IdentNode, arr_type: IdentNode, contained: ExprListNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.type = arr_type
        self.contained = contained
        self.type.name += '[{0}]'.format(contained.length)

    @property
    def children(self):
        return self.name, self.type, self.contained

    def __str__(self) -> str:
        return '='


class VarsListNode(AstNode):
    def __init__(self, *vars_list,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.vars_list = vars_list

    @property
    def children(self):
        return self.vars_list

    def __str__(self) -> str:
        return 'vars'


class FuncDeclNode(AstNode):
    def __init__(self, name: IdentNode, params: VarsListNode, stmts: Optional[StmtListNode] = None,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.params = params if params else _empty
        self.stmts = stmts if stmts else _empty

    @property
    def children(self):
        return self.name, self.params, self.stmts

    def __str__(self) -> str:
        return '='


class FuncNode(AstNode):
    def __init__(self, access: IdentNode, type: IdentNode, inner: FuncDeclNode, static: Optional[IdentNode] = None,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.access = access
        self.static = type if static else _empty
        self.type = type if not static else inner
        self.inner = inner if not static else static

    @property
    def children(self):
        return self.access, self.static, self.type, self.inner

    def __str__(self) -> str:
        return 'func'


_empty = StmtListNode()
