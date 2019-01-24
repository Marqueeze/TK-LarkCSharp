from typing import *


class FunctionCode:
    def __init__(self, name: str, r_type, *params):
        super().__init__()
        self.func_name = name
        self.return_type = r_type
        self.params = []
        self.variables = {}
        self.main_block = []
        self.counter = len(params) + 1
        self.main_code = ''
        self.declaration_block = []
        self.return_ptr = ''
        self.decl_code = ''
        self.align_dict = {}
        self.set_params(params)

    def add_alloc(self, decl_code: Tuple):
        self.decl_code += '  %{0} = alloca {1}, align {2}'.format(self.counter, *decl_code[:-1]) + '\n'
        var_name = decl_code[2]
        if var_name not in self.variables.keys():
            self.variables[var_name] = [*decl_code[:-1], self.counter]
        else:
            self.main_code += '  store {0} %{2}, {0}* %{3}, align {1}\n'.format(*self.variables[var_name],
                                                                                self.counter)
            self.variables[var_name][2] = self.counter
        if decl_code[0] not in self.align_dict.keys():
            self.align_dict[decl_code[0]] = decl_code[1]
        self.counter += 1

    def add_operation(self, op_code: Tuple):
        self.main_block.append(op_code)

    def set_params(self, params):
        for i, param in enumerate(params):
            self.variables[param[2]] = [*param[:-1], i]
            self.params.append(param[0])
            self.add_alloc(param)

    def generate(self) -> str:
        func_code = 'define {0} @{1}({2})'.format(self.return_type, self.func_name, ', '.join(self.params))
        func_code += ' {' + '\n'
        self.generate_inner(self.main_block)
        return ''

    def generate_inner(self, op_list: List):
        try:
            if len(op_list) > 0:
                op = op_list.pop(0)
                func = getattr(self, op[0] + '_')
                return func(op, op_list)
        except AttributeError:
            print(self.main_code)
            raise AttributeError

    def var_(self, op: Tuple, op_list: List):
        if op[1][0] == '@':
            return False, (op[1], '')

        var = self.variables[op[1][1:]]
        self.main_code += '  %{0} = load {1}, {1}*, %{2}, align {3}\n'.format(self.counter, var[0], var[2], var[1])
        self.counter += 1
        return True, var[0]

    def const_(self, op: Tuple, op_list: List):
        return False, (op[1], op[2])

    def binop_(self, op: Tuple, op_list: List):
        arg1_end_index = self.find('end_arg1', op[0], op_list)
        arg2_end_index = self.find('end_arg2', op[0], op_list)

        arg1_list, arg2_list = op_list[: arg1_end_index], op_list[arg1_end_index: arg2_end_index]

        arg1, v_type = self.get_arg(arg1_list)
        arg2, _ = self.get_arg(arg2_list)

        del op_list[:arg2_end_index]

        self.main_code += '  %{0} = {1} {2} {3}, {4}\n'.format(self.counter, op[1], v_type, arg1, arg2)
        self.counter += 1

        return True, v_type if op[1] in ('add', 'mul', 'sdiv', 'sub') else 'i1'

    def get_arg(self, arg_list):
        arg_list.pop()
        res, arg = self.generate_inner(arg_list)

        if res:
            return '%' + str(self.counter - 1), arg
        return arg[0], arg[1]

    def assign_(self, op: Tuple, op_list: List):
        var_index = self.find('end_assign_var', op[0], op_list)
        val_index = self.find('end_assign_val', op[0], op_list)

        var_list, val_list = op_list[: var_index], op_list[var_index: val_index]

        var, v_type = self.get_arg(var_list)
        val, _ = self.get_arg(val_list)

        del op_list[: val_index]

        self.main_code += '  store {0} {1} {0}* {2}, align {3}\n'.format(v_type, val, var, self.align_dict[v_type])
        self.counter += 1

        return self.generate_inner(op_list)

    def if_(self, op: Tuple, op_list: List):
        whole_index = self.find('end_if', op[0], op_list)
        if_list = op_list[: whole_index]

        del op_list[: whole_index]

        cond_index = self.find('then', op[0], if_list) - 1
        then_index = self.find('else', op[0], if_list) - 1

        cond_list = if_list[: cond_index]
        then_list = if_list[cond_index + 1: then_index]

        self.generate_inner(cond_list)
        self.main_code += '  br i1 %{0}, label %{1}, label %{2}\n\n'.format(self.counter - 1, self.counter, '{0}')
        self.main_code += '{0}:\n'.format(self.counter)
        self.counter += 1

        self.generate_inner(then_list)
        self.main_code += '  br label %{1}\n\n'
        self.main_code += '{0}:\n'.format(self.counter)
        else_counter = self.counter
        self.counter += 1

        is_else = if_list[then_index][1]
        if is_else:
            else_list = if_list[then_index + 1: -1]
            self.generate_inner(else_list)
            self.main_code += '  br label %{1}\n\n'
            self.main_code += '{0}:'.format(self.counter)
            self.main_code = self.main_code.format(else_counter, self.counter)
        else:
            self.main_code = self.main_code.format(else_counter, else_counter)

        self.counter += 1

        return self.generate_inner(op_list)

    def while_(self, op: Tuple, op_list: List):
        end_index = self.find('end_while', op[0], op_list)
        while_list = op_list[: end_index]

        del op_list[: end_index]

        cond_index = self.find('while_body', op[0], while_list) - 1

        cond_list = while_list[: cond_index]
        body_list = while_list[cond_index + 1: -1]

        self.main_code += '  br label %{0}\n\n{0}:\n'.format(self.counter)
        cond_label = self.counter
        self.counter += 1

        self.generate_inner(cond_list)
        self.main_code += '  br i1 %{0}, label %{1}, label %{2}\n\n{1}:\n'.format(self.counter - 1, self.counter, '{0}')

        self.generate_inner(body_list)
        self.main_code += '  br label %{1}\n\n{0}:\n'
        self.main_code = self.main_code.format(self.counter, cond_label)
        self.counter += 1

        return self.generate_inner(op_list)

    def find(self, query: str, op: str, op_list):
        support_stack = []
        for i, list_op in enumerate(op_list):
            if list_op[0] == op:
                support_stack.append(1)
            if list_op[0] == query:
                if len(support_stack) == 0:
                    return i + 1
                else:
                    support_stack.pop()

    def get_blocks(self):
        print(self.decl_code)
        print(self.main_code)
