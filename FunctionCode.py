from typing import *
from collections import deque


class FunctionCode:
    def __init__(self, name: str, r_type=None, *params):
        self.func_name = name
        self.return_type = r_type
        self.params = params
        self.declaration_block = []
        self.main_block = deque()
        self.return_ptr = ''
        self.code = ''

    def add_decl(self, decl_code: str):
        self.declaration_block.append(decl_code)

    def add_operation(self, bin_op_code: Tuple):
        self.main_block.extend(bin_op_code)

    def generate_declarations(self):
        for decl in self.declaration_block:
            pass
