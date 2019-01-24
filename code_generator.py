from mel_ast import *
from FunctionCode import FunctionCode


class CodeGenerator:
    def __init__(self, tree: AstNode, output: str):
        self.tree = tree
        self.out = output
        self.llvm_code = ''
        self.constants = ''
        self.const_count = 0
        self.array_count = 0
        self.array_const_func = ''
        self.func_code_list = []
        self.llvm_non_array_types = {'int': ('i32', '4'), 'bool': ('i1', '1'), 'double': ('double', '8'),
                                     'void': ('void', ''), 'char': ('i8', '8'), 'string': ('i8*', '8')}
        self.llvm_scope_types = {'global': '@', 'local': '%', 'param': '%'}
        self.binops = {
            '+':  'add',
            '-':  'sub',
            '*':  'mul',
            '/':  'sdiv',
            '==': 'icmp eq',
            '!=': 'icmp ne',
            '>':  'icmp sgt',
            '>=': 'icmp sge',
            '<':  'icmp slt',
            '<=': 'icmp sle',
            '&&': 'and',
            '||': 'or'
        }

    def generate(self):
        self.generate_inner(self.tree)
        print(self.constants)

    def generate_inner(self, node: AstNode, current: FunctionCode = None):
        if len(node.children) > 0:
            if isinstance(node, BinOpNode):
                self.generate_bin_op(node, current)
            elif isinstance(node, VarsDeclNode):
                self.generate_vars_decl(node, current)
            elif isinstance(node, TypedFuncDeclNode):
                self.generate_function(node)
            elif isinstance(node, AssignNode):
                self.generate_assign(node, current)
            elif isinstance(node, (IfNode, WhileNode, DoWhileNode, ForNode)):
                self.generate_conditionals(node, current)
            elif isinstance(node, TypedArrayDeclNode):
                self.generate_array(node, current)
            elif isinstance(node, IndexNode):
                self.generate_index(node, current)
            elif isinstance(node, CastNode):
                self.generate_cast(node, current)
            elif isinstance(node, CallNode):
                self.generate_call(node, current)
            else:
                for child in node.children:
                    self.generate_inner(child, current)
        else:
            if current:
                if isinstance(node, TypedNode):
                    scope_type = self.llvm_scope_types[node.s_type]
                    var_name = scope_type + node.name
                    current.add_operation(('var', var_name))
                elif isinstance(node, ConstNode):
                    v_type = self.get_ptr_type(node.v_type)[0]
                    if node.v_type.type == 'char':
                        const = str(ord(node.val))
                    elif node.v_type.type == 'bool':
                        const = str(node.val).lower()
                    elif node.v_type.type == 'string':
                        const_name = '@.str_{0}'.format(self.const_count)
                        str_len = len(node.val) + 1
                        self.constants += const_name
                        self.const_count += 1
                        self.constants += self.get_str_const(str_len, node.val)
                        const = ' getelementptr inbounds ([{0} x i8], [{0} x i8]* {1}, i64 0, i64 0)'.format(str_len,
                                                                                                             const_name)
                    else:
                        const = str(node.val)
                    current.add_operation(('const', const, v_type))

    def generate_with_func_code(self):
        pass

    def generate_bin_op(self, node: BinOpNode, current: FunctionCode = None):
        if current:
            current.add_operation(('binop', self.binops[str(node)]))
            self.generate_inner(node.arg1, current)
            current.add_operation(('end_arg1', ))
            self.generate_inner(node.arg2, current)
            current.add_operation(('end_arg2', ))
        pass

    def generate_vars_decl(self, node: VarsDeclNode, current: FunctionCode = None):
        if current:
            v_type = node.vars_type.name
            if v_type in self.llvm_non_array_types.keys():
                llvm_type = self.llvm_non_array_types[v_type]
                for var in node.vars_list:
                    if isinstance(var, TypedNode):
                        current.add_alloc((*llvm_type, var.name))
                    else:
                        current.add_alloc((*llvm_type, var.name.name))
                        self.generate_inner(var, current)
            else:
                v_type = self.llvm_non_array_types[v_type[:-2]][0]
                llvm_type = ['[{0} x {1}]', '16' if v_type not in ('i8', 'i1') else '1']
                for var in node.vars_list:
                    llvm_type[0] = llvm_type[0].format(var.length.val, v_type)
                    current.add_alloc((*llvm_type, var.name.name))
                    self.generate_inner(var, current)
        pass

    def generate_assign(self, node: AssignNode, current: FunctionCode = None):
        if current:
            current.add_operation(('assign', ))
            self.generate_inner(node.name, current)
            current.add_operation(('end_assign_var', ))
            self.generate_inner(node.val, current)
            current.add_operation(('end_assign_val', ))
        pass

    def generate_conditionals(self, node: Union[IfNode, WhileNode, ForNode, DoWhileNode], current: FunctionCode):
        if isinstance(node, IfNode):
            current.add_operation(('if', ))
            self.generate_inner(node.cond, current)

            current.add_operation(('then', ))
            self.generate_inner(node.then_stmt, current)

            current.add_operation(('else', True if node.else_stmt else False))
            if node.else_stmt:
                self.generate_inner(node.else_stmt, current)

            current.add_operation(('end_if', ))

        elif isinstance(node, ForNode):
            current.add_operation(('for', ))
            self.generate_inner(node.init, current)

            current.add_operation(('cond_for', ))
            self.generate_inner(node.cond, current)

            current.add_operation(('step_for', ))
            self.generate_inner(node.step, current)

            current.add_operation(('body_for', ))
            self.generate_inner(node.body, current)

            current.add_operation(('end_for',))

        elif isinstance(node, WhileNode):
            current.add_operation(('while', ))
            self.generate_inner(node.cond, current)

            current.add_operation(('while_body', ))
            self.generate_inner(node.body, current)

            current.add_operation(('end_while',))
        else:
            current.add_operation(('do_while', ))
            self.generate_inner(node.body, current)

            current.add_operation(('do_while_cond', ))
            self.generate_inner(node.cond, current)

            current.add_operation(('end_do_while',))

    def generate_array(self, node: TypedArrayDeclNode, current: FunctionCode = None):
        if current:
            if len(node.contents) > 0:
                current.add_operation(('array', len(node.contents)))
                for i, val in enumerate(node.contents):
                    self.generate_inner(val, current)
                    current.add_operation(('array_idx_{0}'.format(i), ))
        pass

    def generate_index(self, node: IndexNode, current: FunctionCode = None):
        if current:
            current.add_operation(('index', node.ident.name))
            self.generate_inner(node.index)
            current.add_operation(('end_index', ))
        pass

    def generate_cast(self, node: CastNode, current: FunctionCode = None):
        if current:
            current.add_operation(('cast', node.from_.type, node.to_.type))
            self.generate_inner(node.what, current)
            current.add_operation(('end_cast', ))
        pass

    def generate_function(self, node: TypedFuncDeclNode):
        params = [(*self.get_ptr_type(x.vars_list[0].v_type), x.vars_list[0].name) for x in node.params]
        func_code = FunctionCode(node.name, self.llvm_non_array_types[node.r_type.type], *params)
        for stmt in node.stmts:
            self.generate_inner(stmt, func_code)

        func_code.get_blocks()
        func_code.generate()
        self.func_code_list.append(func_code)

    def generate_call(self, node: CallNode, current: FunctionCode = None):
        if current:
            param_types = [self.get_ptr_type(x)[0] for x in node.func.param_types]
            r_type = self.get_ptr_type(node.func.r_type)[0]
            current.add_operation(('call', node.func.name, r_type, param_types))
            for i, param in enumerate(node.params):
                self.generate_inner(param, current)
                current.add_operation(('end_call_param_{0}'.format(i), ))
        pass

    def get_ptr_type(self, t: BaseType):
        if t.isArray:
            v_type = self.llvm_non_array_types[t.type][0]
            return v_type + '*', '8'
        else:
            return self.llvm_non_array_types[t.type]

    def get_str_const(self, length: int, string: str, is_array=False) -> str:
        if is_array:
            return ''
        return ' constant [{0} x i8] c"{1}\\00", align 1'.format(length, string)
