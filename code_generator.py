from mel_ast import *
from scope import Scope


class CodeGenerator:
    def __init__(self, filename):
        self.output_file = open(filename + '.j', 'w')
        self.current_l = {}
        self.types_prefixes_dict = {
            'int': 'I',
            'bool': 'Z',
            'long': 'J',
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

    def write(self, str):
        self.output_file.write(str.lower())

    def generate(self, prog):
        self.write(".class public Test\r\n")
        self.write(".super java/lang/Object\r\n")
        self.generate_props(prog)
        self.write("\r\n\r\n")
        self.generate_init()
        self.generate_funcs()
        self.write("\r\n")
        self.output_file.close()

    def generate_props(self, tree):
        self.cur_tree[0] = []
        for child in tree.children:
            if isinstance(child, VarsDeclNode):
                self.generate_prop(child)
            else:
                self.cur_tree[0].append(child)

    def generate_prop(self, node):
        param_string = ".field "
        shift = len(node.children[0].name)
        if isinstance(node.vars_list[0], AssignNode) or isinstance(node.vars_list[0], TypedArrayDeclNode):
            self.cur_tree[0].append(node.vars_list[0])
        if '[]' in node.children[0].name:
            param_string += "["
            shift = -2
        self.write(param_string + "{0} {1}\r\n".format(
            self.types_prefixes_dict[node.children[0].name[:shift]],
            node.children[1].name.name))
        self.scope.vars[node.children[1].name.name] = "test.{0} {1}" \
            .format(node.children[1].name.name,
                    self.types_prefixes_dict[node.children[0].name[:shift]])

    @staticmethod
    def generate_new_l(scope, req_l=None):
        if req_l is not None:
            return req_l
        try:
            scope.vars[1] += 1
        except KeyError:
            scope.vars[1] = 0
        return scope.vars[1]

    def generate_init(self):
        self.write(".method public <init>()V\r\n")
        self.write("L{0}:\r\n".format(self.generate_new_l(self.scope)))
        self.write("ALOAD 0\r\n")
        self.write("INVOKESPECIAL java/lang/Object/<init>()V\r\n")
        self.cur_tree[1] = []
        for node in self.cur_tree[0]:
            if isinstance(node, AssignNode) or isinstance(node, TypedArrayDeclNode):
                self.write("L{0}:\r\n".format(self.generate_new_l(self.scope)))
                self.initialize_prop(node)
            else:
                self.cur_tree[1].append(node)
        self.write("RETURN\r\n.end method\r\n\r\n")

    def initialize_prop(self, node):
        self.write("ALOAD 0\r\n")
        if '[]' in str(node):
            self.fill_value_and_its_type(node.length.val)
            self.separate_string_array_from_int_array(node)
            self.fill_array(node)
            self.put_array_in_scope(node, self.scope)
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
        self.write("NEW java/lang/StringBuilder\r\n" + "DUP\r\n" +
                   "INVOKESPECIAL java/lang/StringBuilder.<init>()V\r\n")
        self.get_var_value(op.arg1, scope)
        self.write("INVOKEVIRTUAL java/lang/StringBuilder.append" +
                   "(Ljava/lang/String;)Ljava/lang/StringBuilder;\r\n")
        self.get_var_value(op.arg2, scope)
        self.write("INVOKEVIRTUAL java/lang/StringBuilder.append"
                   + "(Ljava/lang/String;)Ljava/lang/StringBuilder;\r\n"
                   + "INVOKEVIRTUAL java/lang/StringBuilder.toString()Ljava/lang/String;\r\n")
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
        elif type(var) == IndexNode:
            self.fill_value_and_its_type(var.index.value)
        elif type(var) == CallNode:
            self.generate_func_call(var, scope, True)
        elif type(var) == CastNode:
            self.generate_cast(var, scope)
        elif scope.parent is None:
            self.get_global_var_value(var.name)
        else:
            self.get_local_var_value(var, scope)

    def get_global_var_value(self, name):
        self.write("ALOAD 0\r\n")
        self.write("GETFIELD " + str(self.scope.vars[name]) + "\r\n")

    def get_local_var_value(self, var, scope):
        try:
            self.write("{0}LOAD {1}\r\n".format(self.types_return_dict[var.v_type.type],
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
        self.write("{0}{1}\r\n".format(self.types_prefixes_dict[binop.arg1.v_type.type],
                                       ops_dict[binop.op.value]))
        return TypedNode("", binop.arg1.v_type, s_type="")

    def cast_itself(self, cast):
        self.write("{0}2{1}\r\n".format(self.types_prefixes_dict[cast._from.type],
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
        self.write(".method {0} {1}({2}){3}\r\n".format(node.access.name, node.name.name,
                                                        ''.join(self.types_prefixes_dict[x.vars_type.name]
                                                                for x in node.params),
                                                        self.types_prefixes_dict[node.r_type.type]))
        self.put_params_in_scope(node.params, self.scope.funcs[node.name.name])
        L = None
        returns = False
        for stmt in node.stmts:
            returns |= type(stmt) == ReturnNode
            L = self.generate_statement(stmt, self.scope.funcs[node.name.name], L)
        if not returns and node.r_type.type == "void":
            self.generate_statement(ReturnNode(), self.scope.funcs[node.name.name], L)

    def put_params_in_scope(self, params, scope):
        for param in params:
            self.put_param_in_scope(param.children[1].name, param.vars_type.token, scope)

    @staticmethod
    def put_param_in_scope(param_name, param_type, scope):
        scope.var_counter += 1
        scope.vars[param_name] = scope.var_counter
        if param_type == 'double':
            scope.var_counter += 1

    def generate_statement(self, node, scope, L=None):
        if type(node) != AbstractNode:
            if L != -1:
                cond_l = self.generate_new_l(scope, L)
                self.write("L{0}:\r\n".format(cond_l))
        if type(node) == ReturnNode:
            self.generate_return(node, scope)
            return None
        elif type(node) == VarsDeclNode:
            return self.generate_vars_decl_node(node, scope)
        elif type(node) == CallNode:
            if node.func.name.lower() == 'readline':
                self.generate_input()
            elif node.func.name.lower() == 'writeline':
                self.generate_output(node.params[0], scope)
            else:
                self.generate_func_call(node, scope)
            return None
        elif type(node) == AssignNode:
            self.generate_assign(node, scope)
            return None
        elif type(node) == IfNode:
            return self.generate_if(node, scope)
        elif type(node) == WhileNode:
            return self.generate_while(node, scope, cond_l)
        elif type(node) == DoWhileNode:
            self.generate_dowhile(node, scope, cond_l)
        elif type(node) == ForNode:
            return self.generate_for(node, scope)
        elif type(node) == AbstractNode:
            for child in node.ch:
                self.generate_statement(child, scope, L)
            return None
        else:
            raise Exception("GOT ANOTHER STATEMENT (codeGen line 196)")

    def generate_func_call(self, call, scope, assigning=False):
        if call.func.name.lower() not in ("str", "write", "writeline", "read", "readline"):
            self.write("ALOAD 0\r\n")
        for param in call.params:
            self.get_var_value(param, scope)
        self.write("INVOKEVIRTUAL test.{0}({1}){2}\r\n"
                   .format(call.func.name,
                           ''.join(self.types_prefixes_dict[x.type] for x in call.func.param_types),
                           self.types_prefixes_dict[call.func.r_type.type]))
        if not assigning and call.func.r_type.type != 'void':
            self.write("POP\r\n")

    def generate_return(self, node, scope):
        if type(node.expr) == BinOpNode:
            self.generate_binop(node.expr, scope)
            self.write("{0}RETURN\r\n".format(self.types_return_dict[node.expr.arg1.v_type.type]))
        elif type(node.expr) == TypedNode:
            r_type = self.types_return_dict[node.expr.v_type.type]
            self.write("{0}LOAD {1}\r\n".format(r_type, scope.vars[node.expr.name]))
            self.write("{0}RETURN\r\n".format(r_type))
        elif type(node.expr) == ConstNode:
            self.fill_value_and_its_type(node.expr.val)
            self.write("{0}RETURN\r\n".format(self.types_return_dict[node.expr.v_type.type]))
        elif type(node.expr) == StmtListNode:
            self.write("RETURN\r\n")
        else:
            raise Exception("RETURNING SMTHN ELSE (codeGen 197)")
        self.write(".end method\r\n")

    def fill_value_and_its_type(self, value):
        if type(value) == bool:
            self.write("{0}_{1}\r\n".format("ICONST", "1" if str(value) == "True" else "0"))
        elif type(value) == str:
            self.write("{0} \"{1}\"\r\n".format("LDC", value))
        else:
            _ = int(value)
            if _ != value:
                self.write("{0} {1}\r\n".format("LDC2_W", value))
            else:
                self.write("{0} {1}\r\n".format(self.number_type(value), value))

    @staticmethod
    def number_type(number):
        number_type = "LDC2_W"
        if abs(number) <= 127:
            number_type = "BIPUSH"
        elif abs(number) <= 32767:
            number_type = "SIPUSH"
        return number_type

    def separate_string_array_from_int_array(self, node):
        if 'string' in str(node).lower():
            self.write("ANEWARRAY java/lang/String\r\n")
        else:
            self.write("NEWARRAY {0}\r\n".format(node.type.v_type))

    def fill_array(self, node):
        for i in range(0, len(node.contents)):
            self.write("DUP\r\n")
            self.write("{0} {1}\r\n".format(self.number_type(i), i))
            self.write("{0} {1}\r\n".format(self.number_type(node.contents[i].val), node.contents[i].val))
            self.write("{0}ASTORE\r\n".format(self.types_prefixes_dict[node.type.v_type]))

    def put_array_in_scope(self, node, scope):
        if scope != self.scope:
            self.put_param_in_scope(node.name.name, str(node.type), scope)
            self.write("ASTORE {0}\r\n".format(self.get_var_value(node.name, scope)))
        # else:
        #     self.putfield(node)

    def putfield(self, node):
        self.write("PUTFIELD test.{0}  {1}\r\n".format(str(node.name.name), self.field_type(node)))

    def field_type(self, node):
        return '[{0}'.format(self.types_prefixes_dict[node.type.v_type]) \
            if '[]' in str(node) else \
            self.types_prefixes_dict[node.name.v_type.v_type]

    def generate_vars_decl_node(self, node, scope):
        if type(node.children[1]) == AssignNode:
            name = node.children[1].name.name
            self.put_param_in_scope(name, node.children[1].name.v_type.type, scope)
            for child in node.children:
                if type(child) == AssignNode:
                    self.generate_assign(child, scope)
                elif type(child) == IdentNode:
                    pass
                else:
                    raise Exception("codeGen line 252")
        elif type(node.children[1]) == TypedNode:
            self.put_param_in_scope(node.children[1].name, node.children[1].v_type.type, scope)
            return -1

    def generate_assign(self, node, scope):
        if type(node.val) == BinOpNode:
            self.generate_binop(node.val, scope)
        elif type(node.val) == CastNode:
            self.generate_cast(node.val, scope)
        elif type(node.val) == CallNode:
            if node.val.func.name.lower() == 'readline':
                self.generate_input()
            elif node.val.func.name.lower() == 'writeline':
                self.generate_output()
            else:
                self.generate_func_call(node.val, scope, True)
        elif type(node.val) in (ConstNode, TypedNode):
            self.get_var_value(node.val, scope)
        elif type(node.val) == InputNode:
            self.generate_input()
        elif type(node.val) == OutputNode:
            self.generate_output(node.val, scope)
        elif type(node.val) == IndexNode:
            self.generate_index(node.val, scope)
        else:
            raise Exception("ASSIGNING SMTH ELSE codeGen 263")
        self.write("{0}{1}STORE {2}\r\n".format(self.types_return_dict[node.name.v_type.type],
                                                "A" if node.name.v_type.isArray else "",
                                                scope.vars[node.name.name]))

    def generate_index(self, index, scope):
        self.get_var_value(index.ident, scope)
        self.get_var_value(index.index, scope)
        self.write("{0}ALOAD\r\n".format(self.types_return_dict[index.ident.v_type.type]))



    def generate_if(self, node, scope):
        # self.write("L{0}\r\n".format(self.generate_new_l(scope)))
        self.get_var_value(node.cond.arg1, scope)
        self.get_var_value(node.cond.arg2, scope)
        else_L = self.generate_cond(node.cond.op.value, node.cond.arg1.v_type.type, scope, "reverse")
        got_else = node.else_stmt is not None
        after_else_L = self.generate_then(node.then_stmt, scope, got_else)
        if got_else:
            self.generate_else(node.else_stmt, scope, else_L)
        else:
            after_else_L = else_L
        return after_else_L

    def generate_else(self, stmt, scope, L=None):
        for i in range(len(stmt.ch)):
            self.generate_statement(stmt.ch[i], scope, L if i == 0 else None)

    def generate_then(self, stmt, scope, got_else):
        for child in stmt.ch:
            self.generate_statement(child, scope)
        L = self.generate_new_l(scope)
        if got_else:
            self.write("GOTO L{0}\r\n".format(L))
        return L

    def generate_cond(self, cond, type, scope, cond_type, req_l=None):
        L = self.generate_new_l(scope) if req_l is None else req_l
        cond_reverse_dict = {
            '<': 'GE',
            '>': 'LE',
            '<=': 'GT',
            '>=': 'LT',
            '==': 'NE',
            '!=': 'EQ',
        }
        cond_straight_dict = {
            '<': 'LT',
            '>': 'GT',
            '<=': 'LE',
            '>=': 'GE',
            '==': 'EQ',
            '!=': 'NE',
        }
        if type == 'string':
            if cond in ('==', '!='):
                outp = "IF_ACMP{0} L{1}\r\n"
            else:
                raise Exception("Wrong string comparing (codeGen 322)")
            self.write(outp.format(eval("cond_" + cond_type + "_dict[cond]"), L))
        elif type in ('int', 'bool'):
            self.write("IF_ICMP{0} L{1}\r\n".format(eval("cond_" + cond_type + "_dict[cond]"), L))
        elif type in ('double', 'long'):
            if type == 'double':
                if cond in ('==', '!=', '>=', '>'):
                    self.write("DCMPL\r\n")
                elif cond in ('<=', '<'):
                    self.write("DCMPG\r\n")
            else:
                self.write("LCMP\r\n")
            self.write("IF{0} L{1}\r\n".format(eval("cond_" + cond_type + "_dict[cond]"), L))
        return L

    def generate_while(self, node, scope, cond_l):
        self.get_var_value(node.cond.arg1, scope)
        self.get_var_value(node.cond.arg2, scope)
        outloop = self.generate_cond(node.cond.op.value, node.cond.arg1.v_type.type, scope, "reverse")
        self.generate_while_body(node.body, scope, cond_l)
        return outloop

    def generate_while_body(self, stmt, scope, cond_l):
        self.generate_else(stmt, scope, cond_l)
        self.write("GOTO L{0}\r\n".format(cond_l))

    def generate_dowhile(self, node, scope, cond_l):  # Body - условие, Cond - действия
        self.generate_dowhile_body(node.cond, scope)
        self.write("L{0}:\r\n".format(self.generate_new_l(scope)))
        self.get_var_value(node.body.arg1, scope)
        self.get_var_value(node.body.arg2, scope)
        self.generate_cond(node.body.op.value, node.body.arg1.v_type.type, scope, "straight", cond_l)

    def generate_dowhile_body(self, cond, scope):
        self.generate_else(cond, scope, -1)

    def generate_for(self, node, scope):
        self.generate_for_init(node.init, scope)
        req_l = self.generate_for_cond(node.cond, scope)
        self.generate_for_body(node.body, scope)
        self.generate_for_step(node.step, scope, req_l[0])
        return req_l[1]

    def generate_for_init(self, node, scope):
        # for ch in node.children:
        #     if type(ch) is not IdentNode:
        self.generate_statement(node, scope, -1)

    def generate_for_cond(self, node, scope):
        L = self.generate_new_l(scope)
        self.write("L{0}:\r\n".format(L))
        self.get_var_value(node.arg1, scope)
        self.get_var_value(node.arg2, scope)
        return L, self.generate_cond(node.op.value, node.arg1.v_type.type, scope, "reverse")

    def generate_for_body(self, body, scope):
        for ch in body.ch:
            self.generate_statement(ch, scope)

    def generate_for_step(self, node, scope, req_l):
        for ch in node.ch:
            self.generate_statement(ch, scope)
        self.write("GOTO L{0}\r\n".format(req_l))

    def generate_input(self):
        self.write('NEW java/io/BufferedReader\r\n'
                   + 'DUP\r\n'
                   + 'NEW java/io/InputStreamReader\r\n'
                   + 'DUP\r\n'
                   + 'GETSTATIC java/lang/System.in  Ljava/io/InputStream;\r\n'
                   + 'INVOKESPECIAL java/io/InputStreamReader.<init>(Ljava/io/InputStream;)V\r\n'
                   + 'INVOKESPECIAL java/io/BufferedReader.<init>(Ljava/io/Reader;)V\r\n'
                   + 'INVOKEVIRTUAL java/io/BufferedReader.readLine()Ljava/lang/String;\r\n')

    def generate_output(self, what, scope):
        self.write('GETSTATIC java/lang/System.out  Ljava/io/PrintStream;\r\n')
        self.get_var_value(what, scope)
        self.write('INVOKEVIRTUAL java/io/PrintStream.println(Ljava/lang/String;)V\r\n')

    def to_string(self, what):
        return "{0}".format(what)
