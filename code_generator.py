from mel_ast import *
from FunctionCode import FunctionCode


class CodeGenerator:
    def __init__(self, tree: AstNode, output: str):
        self.tree = tree
        self.out = output
        self.llvm_code = ''
        self.constants = ''
        self.const_count = 0
        self.llvm_non_array_types = {'int': ('i32', '4'), 'bool': ('i1', '1'),
                                     'double': ('double', '8'), 'void': ('void', ''), 'char': ('i8', '8')}
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
        self.llvm_code = self.generate_inner(self.tree)
        return self.llvm_code

    def generate_inner(self, node: AstNode, func_code: FunctionCode=None) -> Tuple[str, str]:
        code = ''
        v_type = ''
        if len(node.children) > 0:
            if isinstance(node, BinOpNode):
                code, v_type = self.generate_bin_op(node, func_code)
            elif isinstance(node, TypedFuncDeclNode):
                self.generate_function(node)
            else:
                for child in node.children:
                    self.generate_inner(child, func_code)
        else:
            if isinstance(node, ConstNode):
                if node.v_type.type in self.llvm_non_array_types.keys():
                    v_type = self.llvm_non_array_types[node.v_type.type]
                if node.v_type.type == 'char':
                    const = str(ord(node.val))
                elif node.v_type.type == 'bool':
                    const = str(node.val).lower()
                elif node.v_type.type == 'string':
                    const_name = '@.str_{0}'.format(self.const_count)
                    str_len = len(node.val) + 1
                    self.constants += const_name
                    self.const_count += 1
                    self.constants += ' constant [{0} x i8] c"{1}\\00", align 1'.format(str_len, node.val)
                    const = ' getelementptr inbounds ([{0} x i8], [{0} x i8]* {1}, i64 0, i64 0)'.format(str_len,
                                                                                                         const_name)
                else:
                    const = str(node.val)
                code += const
            elif isinstance(node, TypedNode):
                if node.v_type.type in self.llvm_non_array_types.keys():
                    v_type = self.llvm_non_array_types[node.v_type.type]
                scope_type = self.llvm_scope_types[node.s_type]
                code += scope_type + node.name
        return code, v_type

    def generate_with_func_code(self):
        pass

    def get_type(self, node) -> str:
        pass

    def generate_bin_op(self, node: BinOpNode, current: FunctionCode = None):
        if current:
            arg1_code, v_type = self.generate_inner(node.arg1, current)
            arg2_code, _ = self.generate_inner(node.arg2, current)

            current.add_operation((arg2_code, arg1_code, v_type, str(node)))

            return '_' + str(node), v_type
        return '', ''

    def generate_assign(self, node: AssignNode, current: FunctionCode = None):
        pass

    def generate_function(self, node: TypedFuncDeclNode):
        func_code = FunctionCode(node.name)
        for stmt in node.stmts:
            self.generate_inner(stmt, func_code)

        return None
