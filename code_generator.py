from mel_ast import *
from base_type import *


class FunctionCode:
    def __init__(self):
        self.declarations = []
        self.binops = []
        self.code = ''

    def add_decl(self, decl_code: str):
        self.declarations.append(decl_code)

    def add_bin_op(self, bin_op_code: str):
        self.binops.append(bin_op_code)


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

    def generate_inner(self, node: AstNode) -> Tuple[str, str]:
        code = ''
        v_type = ''
        if len(node.children) > 0:
            if isinstance(node, BinOpNode):
                self.generate_bin_op(node)
            else:
                for child in node.children:
                    code_snippet, v_type = self.generate_inner(child)
                    code += code_snippet
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
                    self.constants += ' constant [{0} x i8] c"{1}\\00", align 1'.format(str_len, node.val) + '\n'
                    const = ' getelementptr inbounds ([{0} x i8], [{0} x i8]* {1}, i64 0, i64 0)'.format(str_len,
                                                                                                         const_name)
                else:
                    const = str(node.val)
                code += const + '\n'
            elif isinstance(node, TypedNode):
                if node.v_type.type in self.llvm_non_array_types.keys():
                    v_type = self.llvm_non_array_types[node.v_type.type]
                scope_type = self.llvm_scope_types[node.s_type]
                code += scope_type + node.name + '\n'
        return code, v_type

    def generate_with_func_code(self):
        pass

    def generate_bin_op(self, node: BinOpNode, current: FunctionCode=None):
        code = ''
        op = self.binops[str(node)]
        arg1_snippet, v_type = self.generate_inner(node.arg1)
        arg2_snippet, _ = self.generate_inner(node.arg2)

        current.add_bin_op('{0} {1} {2}, {3}'.format(op, v_type, arg1_snippet, arg2_snippet))

    def get_type(self, node) -> str:
        pass

