from abc import ABC, abstractmethod
from typing import Callable, Tuple, Optional, Union
from enum import Enum
from base_type import BaseType


class AstNode(ABC):
    def __init__(self, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__()
        self.row = row
        self.line = line
        self.scope = None
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
        res = [str(self)]
        children_temp = self.children
        for i, child in enumerate(children_temp):
            ch0, ch = '├', '│'
            if i == len(children_temp) - 1:
                ch0, ch = '└', ' '
            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return res

    def visit(self, func: Callable[['AstNode'], None])->None:
        func(self)
        map(func, self.children)

    def __getitem__(self, index):
        return self.children[index] if index < len(self.children) else None


class ExprNode(AstNode):
    pass


class LiteralNode(AstNode):
    def __init__(self, literal: str,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.literal = literal
        self.value = eval(literal)

    def __str__(self)->str:
        return '{0} ({1})'.format(self.literal, type(self.value).__name__)


class IdentNode(AstNode):
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
    NEQUALS = '!='
    EQUALS = '=='
    GT = '>'
    LT = '<'
    BIT_AND = '&'
    BIT_OR = '|'
    LOGICAL_AND = '&&'
    LOGICAL_OR = '||'


class BinOpNode(AstNode):
    def __init__(self, op: BinOp, arg1: AstNode, arg2: AstNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> Tuple[AstNode, AstNode]:
        return self.arg1, self.arg2

    def __str__(self)->str:
        return str(self.op.value)


class StmtNode(AstNode):
    pass


class VarsDeclNode(AstNode):
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


class CallNode(AstNode):
    def __init__(self, func: AstNode, *params: Tuple[ExprNode],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.func = func
        self.params = params

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return self.func, (*self.params)

    def __str__(self)->str:
        return 'call'


class AssignNode(AstNode):
    def __init__(self, var: AstNode, val: AstNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = var
        self.val = val

    @property
    def children(self) -> Tuple[AstNode, AstNode]:
        return self.name, self.val

    def __str__(self)->str:
        return '='


class IfNode(AstNode):
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


class ForNode(AstNode):
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


class StmtListNode(AstNode):
    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.exprs = exprs

    @property
    def children(self) -> Tuple[StmtNode, ...]:
        return self.exprs

    def __str__(self)->str:
        return '...'


class WhileNode(AstNode):
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


class DoWhileNode(AstNode):
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


class ArrayNode(AstNode):
    def __init__(self, name: IdentNode, arr_type: IdentNode, contained: ExprListNode, length: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.type = arr_type
        self.length = length
        self.contained = contained
        # self.type.name += '[{0}]'.format(length)

    @property
    def children(self):
        return self.name, self.type, self.length, self.contained

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
    def __init__(self, name: IdentNode, params: VarsListNode, stmts: Optional[StmtListNode]=None,
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
    def __init__(self, access: IdentNode, type: IdentNode, inner: FuncDeclNode, static: Optional[IdentNode]=None,
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


class ReturnNode(AstNode):
    def __init__(self, expr: AstNode=None,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.expr = expr if expr else _empty

    @property
    def children(self) -> Tuple:
        return self.expr,

    def __str__(self):
        return 'returns'


class IndexNode(AstNode):
    def __init__(self, ident, index,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.ident = ident
        self.index = index

    @property
    def children(self):
        return self.ident, self.index

    def __str__(self):
        return str(self.ident)


class CastNode(AstNode):
    def __init__(self, what: AstNode, _from: BaseType, _to: BaseType,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.what = what
        self._from = _from
        self._to = _to

    @property
    def children(self):
        return self.what,

    def __str__(self):
        return 'cast ({0} -> {1})'.format(self._from, self._to)


class AbstractNode(AstNode):
    def __init__(self, children,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.ch = children

    @property
    def children(self):
        return tuple(self.ch)

    def __str__(self):
        return '...'


class ConstNode(AstNode):
    def __init__(self, val, v_type: BaseType,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.val = val
        self.v_type = v_type

    def __str__(self):
        return '{0}(const, v_type - {1})'.format(str(self.val), self.v_type)


class TypedNode(AstNode):
    def __init__(self, name: str, v_type: BaseType, s_type: str,
                     row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.v_type = v_type
        self.s_type = s_type

    def __str__(self):
        return '{0}(v_type - {1}, s_type - {2})'.format(self.name, self.v_type, self.s_type)


class TypedFuncNode(AstNode):
    def __init__(self, name: str, r_type: BaseType, *param_types,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.r_type = r_type
        self.param_types = param_types

    def __str__(self):
        return '{0}({1} -> {2})'.format(self.name, str([str(t) for t in self.param_types]), self.r_type)


class TypedFuncDeclNode(AstNode):
    def __init__(self, name: str, access: str, r_type: BaseType, stmts, params,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.r_type = r_type
        self.access = access
        self.stmts = stmts
        self.params = params

    @property
    def children(self):
        return tuple(self.params) + tuple(self.stmts)

    def __str__(self):
        return '{0} (returns {1})'.format(self.name, self.r_type)


class TypedArrayDeclNode(AstNode):
    def __init__(self, name, contents, length, _type: BaseType,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.type = _type
        self.length = length
        self.contents = contents

    @property
    def children(self):
        return (self.length, ) + tuple(self.contents)

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.type)


_empty = StmtListNode()
