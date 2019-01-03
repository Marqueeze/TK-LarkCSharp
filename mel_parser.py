from lark import Lark, InlineTransformer
from lark.lexer import Token
from mel_ast import *


parser = Lark('''
    %import common.NUMBER
    %import common.ESCAPED_STRING
    %import common.CNAME
    %import common.NEWLINE
    %import common.WS

    %ignore WS

    COMMENT: "/*" /(.|\\n|\\r)+/ "*/"           
        |  "//" /(.)+/ NEWLINE
    %ignore COMMENT

    num: NUMBER  -> literal
    str: ESCAPED_STRING  -> literal
    ident: CNAME
            | CNAME "[" "]" -> arr

    ADD:     "+"
    SUB:     "-"
    MUL:     "*"
    DIV:     "/"
    AND:     "&&"
    OR:      "||"
    BIT_AND: "&"
    BIT_OR:  "|"
    GE:      ">="
    LE:      "<="
    NEQUALS: "!="
    EQUALS:  "=="
    GT:      ">"
    LT:      "<"

    call: ident "(" ( expr ( "," expr )* )? ")"

    ?group: num 
        | str
        | ident
        | call
        | "(" expr ")"

    ?mult: group
        | mult ( MUL | DIV ) group  -> bin_op

    ?add: mult
        | add ( ADD | SUB ) mult  -> bin_op

    ?compare1: add
        | add ( GT | LT | GE | LE ) add  -> bin_op
        
    ?compare2: compare1
        | compare1 ( EQUALS | NEQUALS ) compare1  -> bin_op

    ?logical_and: compare2
        | logical_and AND compare2  -> bin_op

    ?logical_or: logical_and
        | logical_or OR logical_and  -> bin_op

    ?expr: logical_or
    
    ?expr_list: expr ( "," expr )* -> expr_list

    ?var_decl_inner: ident  -> ident
        | ident "=" expr    -> assign
        | ident "=" "new" ident "[" expr "]" -> array
        | ident "=" "new" ident "{" expr_list "}" -> array
   
    vars_decl: ident var_decl_inner ( "," var_decl_inner )*
        
    ?vars_list: (vars_decl ("," vars_decl )* )? -> vars_list
        
    ?func_decl_inner: ident "(" vars_list ")" "{" stmt_list? "}" -> func_decl
    
    func_decl: ident ident? ident func_decl_inner -> func

    ?simple_stmt: ident "=" expr  -> assign
        | call

    ?for_stmt_list: vars_decl
        | ( simple_stmt ( "," simple_stmt )* )?  -> stmt_list
    ?loop_cond: expr
        |   -> stmt_list
    ?loop_body: stmt
        | ";"  -> stmt_list
        

    ?stmt: vars_decl ";"
        | simple_stmt ";"
        | "if" "(" expr ")" stmt ("else" stmt)?  -> if
        | "for" "(" for_stmt_list ";" loop_cond ";" for_stmt_list ")" loop_body  -> for
        | "while" "(" loop_cond ")" loop_body -> while
        | "do" loop_body "while" "(" loop_cond ")" -> do_while
        | "{" stmt_list "}"
        | func_decl
        | "return" ident -> return
        | "return" expr -> return

    stmt_list: ( stmt ";"* )*

    ?prog: stmt_list

    ?start: prog
''', start='start')  # , parser='lalr')


class MelASTBuilder(InlineTransformer):
    def __getattr__(self, item):
        if item in ('bin_op', ):
            def get_bin_op_node(*args):
                op = BinOp(args[1].value)
                return BinOpNode(op, args[0], args[2],
                                 **{ 'token': args[1], 'line': args[1].line, 'column': args[1].column })
            return get_bin_op_node
        elif item == 'array':
            def get_array_node(*args):
                name = args[0]
                v_type = IdentNode(args[1].name + '[]',
                                   **{'token': args[1], 'line': args[1].line, 'column': args[1].column})
                if isinstance(args[2], LiteralNode):
                    length = args[2]
                    values = ExprListNode(**{'token': args[1], 'line': args[1].line, 'column': args[1].column})
                else:
                    length = LiteralNode(str(args[2].length))
                    values = args[2]
                return ArrayNode(name, v_type, values, length,
                                 **{'token': args[1], 'line': args[1].line, 'column': args[1].column})
            return get_array_node
        elif item == 'arr':
            def get_node(*args):
                props = {}
                if len(args) == 1 and isinstance(args[0], Token):
                    props['token'] = args[0]
                    props['line'] = args[0].line
                    props['column'] = args[0].column
                    args = [args[0].value + '[]']
                return IdentNode(*args, **props)
            return get_node
        else:
            def get_node(*args):
                props = {}
                if len(args) == 1 and isinstance(args[0], Token):
                    props['token'] = args[0]
                    props['line'] = args[0].line
                    props['column'] = args[0].column
                    args = [args[0].value]
                cls = eval(''.join(x.capitalize() for x in item.split('_')) + 'Node')
                return cls(*args, **props)
            return get_node


def parse(prog: str)->StmtListNode:
    prog = parser.parse(str(prog))
    # print(prog.pretty('  '))
    prog = MelASTBuilder().transform(prog)
    return prog
