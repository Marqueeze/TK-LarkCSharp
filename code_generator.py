from mel_ast import *
from scope import Scope


class CodeGenerator:
    def __init__(self):
        self.output_file = open('output.txt', 'w')
        self.current_l = {}
        self.types_prefixes_dict = {
            'int': 'I',
            'bool': 'Z',
            'long': 'L',
            'double': 'D',
            'string': 'Ljava/lang/String;',
            'void': 'V'
        }
        self.types_return_dict = {
            'int': 'I',
            'bool': 'Z',
            'long': 'L',
            'double': 'D',
            'string': 'A',
            'void': 'V'
        }
        self.scope = Scope(parent=None)
        self.cur_tree = dict()

    def generate(self, prog):
        self.output_file.write("class Test{\r\n")
        self.generate_props(prog)
        self.output_file.write("\r\n\r\n")
        self.generate_init()
        self.generate_funcs()
        self.output_file.write("\r\n}")
        self.output_file.close()

    def generate_props(self, tree):
        self.cur_tree[0] = []
        for child in tree.children:
            if isinstance(child, VarsDeclNode):
                self.generate_prop(child)
            else:
                self.cur_tree[0].append(child)

    def generate_prop(self, node):
        param_string = ""
        shift = len(node.children[0].name)
        if isinstance(node.vars_list[0], AssignNode) or isinstance(node.vars_list[0], TypedArrayDeclNode):
            self.cur_tree[0].append(node.vars_list[0])
        if '[]' in node.children[0].name:
            param_string = "["
            shift = -2
        self.output_file.write(param_string + "{0} {1}\r\n".format(
                                                                self.types_prefixes_dict[node.children[0].name[:shift]],
                                                                node.children[1].name.name))
        self.scope.vars[node.children[1].name.name] = "test.{0} : {1}"\
            .format(node.children[1].name.name,
                    self.types_prefixes_dict[node.children[0].name[:shift]])

    def generate_new_l(self, func):
        func_name = func.name.name
        try:
            self.current_l[func_name] += 1
        except KeyError:
            self.current_l[func_name] = 0
        return self.current_l[func_name]

    def generate_init(self):
        self.output_file.write("<init>()V\r\n")
        self.output_file.write("L{0}\r\n".format(self.generate_new_l(FuncDeclNode(IdentNode("0"), ""))))
        self.output_file.write("ALOAD 0\r\n")
        self.output_file.write("INVOKESPECIAL java/lang/Object.<init> ()V\r\n")
        self.cur_tree[1] = []
        for node in self.cur_tree[0]:
            if isinstance(node, AssignNode) or isinstance(node, TypedArrayDeclNode):
                self.output_file.write("L{0}\r\n".format(self.generate_new_l(FuncNode("", "", "",
                                                                             inner=FuncDeclNode("", "", name='0')))))
                self.initialize_prop(node)
            else:
                self.cur_tree[1].append(node)
        self.output_file.write("RETURN\r\n\r\n")

    def initialize_prop(self, node):
        self.output_file.write("ALOAD 0\r\n")
        if '[]' in str(node):
            self.fill_value_and_its_type(node.length.val)
            self.separate_string_array_from_int_array(node)
            self.fill_array(node)
        else:
            if type(node.val) == CastNode:
                self.generate_cast(node.val, self.scope)
            else:
                self.fill_value_and_its_type(node.val.val)
        self.putfield(node)

    def generate_cast(self, cast, scope):
        self.push_castable(cast, scope)
        self.cast_itself(cast)

    def push_castable(self, cast: CastNode, scope):
        if type(cast.what) == BinOpNode:
            self.generate_binop(cast.what, scope)
        elif type(cast.what) == TypedNode:
            self.get_var_value(cast.what, scope)
        else:
            raise Exception("CASTING SMTHIN ELSE codeGen 80")

    def generate_binop(self, binop, scope):
        if type(binop.arg1) == BinOpNode:
            binop.arg1 = self.generate_binop(binop.arg1, scope)
        if type(binop.arg2) == BinOpNode:
            binop.arg2 = self.generate_binop(binop.arg2, scope)
        if binop.arg1.v_type.type == "string":
            if binop.op.value == '+':
                return self.generate_string_op(binop, scope)
            else:
                raise Exception("String concat allowed only codeGen 95")
        else:
            self.put_value_on_stack(binop.arg1, scope)
            self.put_value_on_stack(binop.arg2, scope)
            return self.do_op(binop)

    def generate_string_op(self, op, scope):
        self.output_file.write("NEW java/lang/StringBuilder\r\n" + "DUP\r\n" +
                               "INVOKESPECIAL java/lang/StringBuilder.<init> ()V\r\n")
        self.get_var_value(op.arg1, scope)
        self.output_file.write("INVOKEVIRTUAL java/lang/StringBuilder.append" +
                               " (Ljava/lang/String;)Ljava/lang/StringBuilder;\r\n")
        self.get_var_value(op.arg2, scope)
        self.output_file.write("INVOKEVIRTUAL java/lang/StringBuilder.append "
                               + "(Ljava/lang/String;)Ljava/lang/StringBuilder;\r\n"
                               + "INVOKEVIRTUAL java/lang/StringBuilder.toString ()Ljava/lang/String;\r\n")
        return TypedNode("", op.arg1.v_type, '')

    def put_value_on_stack(self, val, scope):
        if type(val) == ConstNode:
            self.fill_value_and_its_type(val.val)
        elif type(val) == CastNode:
            self.generate_cast(val, scope)
        elif type(val) == TypedNode:
            if val.name != "":
                self.get_var_value(val, scope)
            else:
                pass
        else:
            raise Exception("codeGen 121")

    def get_var_value(self, var, scope):
        if type(var) == ConstNode:
            self.fill_value_and_its_type(var.val)
        elif type(var) == BinOpNode:
            self.generate_binop(var, scope)
        elif scope.parent is None:
            self.get_global_var_value(var.name)
        else:
            self.get_local_var_value(var, scope)

    def get_global_var_value(self, name):
        self.output_file.write("ALOAD 0\r\n")
        self.output_file.write("GETFIELD "+self.scope.vars[name]+"\r\n")

    def get_local_var_value(self, var, scope):
        try:
            self.output_file.write("{0}LOAD {1}\r\n".format(self.types_return_dict[var.v_type.type],
                                                            scope.vars[var.name]))
        except KeyError:
            self.get_var_value(var, scope.parent)

    def do_op(self, binop):
        ops_dict = {
            '+': 'ADD',
            '-': 'SUB',
            '*': 'MUL',
            '/': 'DIV'
        }
        self.output_file.write("{0}{1}\r\n".format(self.types_prefixes_dict[binop.arg1.v_type.type],
                                                   ops_dict[binop.op.value]))
        return TypedNode("", binop.arg1.v_type, s_type="")

    def cast_itself(self, cast):
        self.output_file.write("{0}2{1}\r\n".format(self.types_prefixes_dict[cast._from.type],
                                                    self.types_prefixes_dict[cast._to.type]))

    def generate_funcs(self):
        self.cur_tree[2] = []
        for node in self.cur_tree[1]:
            if type(node) == TypedFuncDeclNode:
                self.generate_func(node)
            else:
                self.cur_tree[2].append(node)

    def generate_func(self, node):
        self.scope.funcs[node.name.name] = Scope(parent=self.scope, name=node.name.name)
        self.output_file.write("{0} {1}({2}){3}\r\n".format(node.access.name, node.name.name,
                                                            ''.join(self.types_prefixes_dict[x.vars_type.name]
                                                                    for x in node.params),
                                                            self.types_prefixes_dict[node.r_type.type]))
        self.put_params_in_scope(node.params, self.scope.funcs[node.name.name])
        for stmt in node.stmts:
            self.output_file.write("L{0}\r\n".format(self.generate_new_l(node)))
            self.generate_statement(stmt, self.scope.funcs[node.name.name])

    def put_params_in_scope(self, params, scope):
        for param in params:
            self.put_param_in_scope(param.children[1].name, param.vars_type.token, scope)

    @staticmethod
    def put_param_in_scope(param_name, param_type, scope):
        scope.var_counter += 1 if param_type != 'double' else 2
        scope.vars[param_name] = scope.var_counter

    def generate_statement(self, node, scope):
        if type(node) == ReturnNode:
            self.generate_return(node, scope)
        elif type(node) == VarsDeclNode:
            self.generate_vars_decl_node(node, scope)
        elif type(node) == CallNode:
            self.generate_func_call(node, scope)
        elif type(node) == AssignNode:
            self.generate_assign(node, scope)
        else:
            raise Exception("GOT ANOTHER STATEMENT (codeGen line 196)")

    def generate_func_call(self, call, scope, assigning=False):
        self.output_file.write("ALOAD 0\r\n")
        for param in call.params:
            self.get_var_value(param, scope)
        self.output_file.write("INVOKEVIRTUAL test.{0} ({1}){2}\r\n"
                               .format(call.func.name,
                                       ''.join(self.types_prefixes_dict[x.type] for x in call.func.param_types),
                                       self.types_prefixes_dict[call.func.r_type.type]))
        if not assigning:
            self.output_file.write("POP\r\n")

    def generate_return(self, node, scope):
        if type(node.expr) == BinOpNode:
            self.generate_binop(node.expr, scope)
            self.output_file.write("{0}RETURN\r\n".format(self.types_return_dict[node.expr.arg1.v_type.type]))
        elif type(node.expr) == TypedNode:
            r_type = self.types_return_dict[node.expr.v_type.type]
            self.output_file.write("{0}LOAD {1}\r\n".format(r_type, scope.vars[node.expr.name]))
            self.output_file.write("{0}RETURN\r\n\r\n".format(r_type))
        elif type(node.expr) == ConstNode:
            self.fill_value_and_its_type(node.expr.val)
            self.output_file.write("{0}RETURN\r\n\r\n".format(self.types_return_dict[node.expr.v_type.type]))
        else:
            raise Exception("RETURNING SMTHN ELSE (codeGen 197)")

    def fill_value_and_its_type(self, value):
        if type(value) == bool:
            self.output_file.write("{0} {1}\r\n".format("ICONST", "1" if str(value) == "True" else "0"))
        else:
            try:
                _ = int(value)
                if _ != value:
                    self.output_file.write("{0} {1}\r\n".format("LDC", value))
                else:
                    self.output_file.write("{0} {1}\r\n".format(self.number_type(value), value))
            except Exception:
                self.output_file.write("{0} \"{1}\"\r\n".format("LDC", value))

    @staticmethod
    def number_type(number):
        number_type = "LDC"
        if abs(number) <= 127:
            number_type = "BIPUSH"
        elif abs(number) <= 32767:
            number_type = "SIPUSH"
        return number_type

    def separate_string_array_from_int_array(self, node):
        if 'string' in str(node).lower():
            self.output_file.write("ANEWARRAY java/lang/String\r\n")
        else:
            self.output_file.write("NEWARRAY T_{0}\r\n".format(node.type.v_type))

    def fill_array(self, node):
        for i in range(0, len(node.contents)):
            self.output_file.write("DUP\r\n")
            self.output_file.write("{0} {1}\r\n".format(self.number_type(i), node.contents[i].val))
            self.output_file.write("{0}ASTORE\r\n".format(self.types_prefixes_dict[node.type.v_type]))

    def putfield(self, node):
        self.output_file.write("PUTFIELD test.{0} : {1}\r\n".format(str(node.name.name), self.field_type(node)))

    def field_type(self, node):
        return '[{0}'.format(self.types_prefixes_dict[node.type.v_type]) \
            if '[]' in str(node) else \
            self.types_prefixes_dict[node.name.v_type.v_type]

    def generate_vars_decl_node(self, node, scope):
        name = node.children[1].name.name
        self.put_param_in_scope(name, scope)
        for child in node.children:
            if type(child) == AssignNode:
                self.generate_assign(child, scope)
            elif type(child) == IdentNode:
                pass
            else:
                raise Exception("codeGen line 252")

    def generate_assign(self, node, scope):
        if type(node.val) == BinOpNode:
            self.generate_binop(node.val, scope)
        elif type(node.val) == CastNode:
            self.generate_cast(node.val, scope)
        elif type(node.val) == CallNode:
            self.generate_func_call(node.val, scope, True)
        elif type(node.val) in (ConstNode, TypedNode):
            self.get_var_value(node.val, scope)
        else:
            raise Exception("ASSIGNING SMTH ELSE codeGen 263")
        self.output_file.write("{0}STORE {1}\r\n".format(self.types_return_dict[node.name.v_type.type],
                                                         scope.vars[node.name.name]))
