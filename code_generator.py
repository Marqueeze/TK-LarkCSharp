from mel_ast import *


class CodeGenerator:
    def __init__(self):
        self.output_file = open('output.txt', 'w')
        self.locals_counter = 1
        self.types_prefixes_dict = {
            'int': 'I',
            'bool': 'Z',
            'long': 'L',
            'double': 'D',
            'string': 'Ljava/lang/String;'
        }
        self.params = dict()
        self.cur_tree = dict()

    def generate(self, prog):
        self.output_file.write("class Test{\r\n")
        self.generate_props(prog)
        self.output_file.write("\r\n\r\n");
        self.output_file.write("<init>()V\r\n")
        self.output_file.write("ALOAD 0\r\n")
        self.output_file.write("INVOKESPECIAL java/lang/Object.<init> ()V\r\n")
        self.generate_init()

        self.output_file.write("}")

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

    def generate_init(self):
        self.cur_tree[1] = []
        for node in self.cur_tree[0]:
            if isinstance(node, AssignNode) or isinstance(node, TypedArrayDeclNode):
                self.initialize_prop(node)
            else:
                self.cur_tree[1].append(node)
        self.output_file.write("RETURN")

    def initialize_prop(self, node):
        self.output_file.write("ALOAD 0\r\n")
        if '[]' in str(node):
            self.fill_value_and_its_type(node.length.val)
            self.separate_string_array_from_int_array(node)
            self.fill_array(node)
        else:
            self.fill_value_and_its_type(node.val.val)
        self.putfield(node)

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
        if 'string' in str(node.children[0]).lower():
            self.output_file.write("ANEWARRAY java/lang/String\r\n")
        else:
            self.output_file.write("NEWARRAY T_{0}\r\n".format(node.type.v_type)) # node.type.v_type - bbb

    def fill_array(self, node):
        for i in range(0, len(node.contents)):
            self.output_file.write("DUP\r\n")
            self.output_file.write("{0} {1}\r\n".format(self.number_type(i), node.contents[i].val))
            self.output_file.write("{0}ASTORE".format(self.types_prefixes_dict[node.type.v_type]))

    def putfield(self, node):
        self.output_file.write("PUTFIELD test.{0}: {1}\r\n".format(str(node.name.name), self.field_type(node)))

    def field_type(self, node):
        return '[{0}'.format(self.types_prefixes_dict[node.type.v_type]) \
            if '[]' in str(node) else \
            self.types_prefixes_dict[node.name.v_type.v_type]

    def generate_vars_decl_node(self, node: VarsDeclNode):
        name = node.children[0].name
        self.params[name] = self.locals_counter
        self.locals_counter += 1
        if '[]' in name:
            self.fill_number_and_its_type(node)
            self.separate_string_array_from_int_array(node)
            self.output_file.write("ASTORE {0}".format(self.params[name]))
        else:
            self.output_file.write("{0}CONST_{1}\r\n".format(self.types_prefixes_dict[str(node.children[0])],
                                                            str(node.children[1].children[1].val)))
            self.output_file.write("{0}STORE {1}".format(self.types_prefixes_dict[str(node.children[0])],
                                                         self.locals_counter))
