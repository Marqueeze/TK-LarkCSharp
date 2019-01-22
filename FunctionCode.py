from typing import *
from collections import deque


class CodeBlock:
    def __init__(self):
        self.variables = {}
        self.main_block = deque()
        self.counter = 0
        self.main_code = ''


class FunctionCode(CodeBlock):
    def __init__(self, name: str, r_type, *params):
        super().__init__()
        self.func_name = name
        self.return_type = r_type
        self.params = []
        self.counter = len(params) + 1
        self.declaration_block = []
        self.return_ptr = ''
        self.decl_code = ''
        self.set_params(params)

    def add_alloc(self, decl_code: Tuple):
        self.decl_code += '%{0} = alloca {1}, align {2}'.format(self.counter, *decl_code[:-1]) + '\n'
        var_name = decl_code[2]
        if var_name not in self.variables.keys():
            self.variables[var_name] = (decl_code[0], self.counter)
        self.counter += 1

    def add_operation(self, op_code: Tuple):
        self.main_block.append(op_code)

    def set_params(self, params):
        for i, param in enumerate(params):
            self.variables[param[2]] = (param[0], i)
            self.params.append(param[0])
            self.add_alloc(param)

    def get_blocks(self):
        print(self.decl_code)
        print(self.variables)
        print(self.main_block)
