import copy

from mel_ast import *
from scope import Scope
from base_type import *
from exception import AnalyzerError


class Analyzer:
    def __init__(self):
        self.scope = Scope(name='global')
        self.scopes = []
        self.type_analogs = {int: Int, str: String, float: Double, bool: Bool}

    def form_scope(self, tree: StmtListNode):
        self.form_scope_inner(tree, self.scope, 'global')

    def form_scope_inner(self, node: AstNode, parent: Scope, s_type: str):
        scope = parent
        if isinstance(node, VarsDeclNode):
            scope = self.vars_decl_scope(scope, str(node.vars_type), s_type, node.vars_list)

        elif isinstance(node, FuncNode):
            if scope.is_func_allowed:
                if self.check_in_scope(scope, str(node.inner.name), 'funcs'):
                    s_type = 'local'
                    return_type = node.type.name
                    node.scope = scope
                    node = node.inner
                    scope.funcs[str(node.name)] = \
                        {'r': return_type, 'p': [str(x.children[0]) for x in node.params.vars_list]}
                    scope = Scope(parent=scope, name=str(node.name))

                    for param in node.params.vars_list:
                        param.scope = self.vars_decl_scope(scope, str(param.vars_type), 'param', param.vars_list)

                    node.scope = scope
                    node = node.stmts

                else:
                    raise AnalyzerError("{0} has already been initialized".format(str(node.inner.name)))
            else:
                raise AnalyzerError("Impossible to initialize functions outside global scope")

        elif isinstance(node, (ForNode, WhileNode, DoWhileNode, IfNode)):
            class_name = node.__class__.__name__
            scope = Scope(parent=scope, name=class_name[: len(class_name) - 4])
            s_type = 'local'

        if len(node.children) > 0:
            for child in node.children:
                self.form_scope_inner(child, scope, s_type)
        else:
            if scope not in self.scopes:
                self.scopes.append(scope)
                self.scopes = [x for x in self.scopes if x != scope.parent]

        node.scope = scope

    def vars_decl_scope(self, scope: Scope, d_type, s_type, nodes: Tuple[AstNode]):
        for node in nodes:
            if isinstance(node, (IdentNode, ArrayNode, AssignNode)):
                if isinstance(node, (ArrayNode, AssignNode)):
                    node.is_reassignment = False
                if self.check_in_scope(scope, str(node.name), 'vars'):
                    scope.vars[str(node.name)] = (d_type, s_type)
                else:
                    raise AnalyzerError("{0} has already been initialized".format(str(node.name)))
            node.scope = scope
        return scope

    def analyze(self, tree: StmtListNode):
        self.form_scope(tree)
        return self.analyze_inner(tree)

    def analyze_inner(self, node: AstNode) -> Union[Tuple[AstNode, BaseType], Tuple[AstNode, None]]:
        if isinstance(node, ReturnNode):
            if node.scope.name == 'global':
                raise AnalyzerError('Nothing to return without a function')
            new_node, v_type = self.analyze_inner(node.expr)
            return ReturnNode(new_node), v_type
        if len(node.children) > 0:
            if isinstance(node, BinOpNode):
                return self.analyze_bin_op(node)
            elif isinstance(node, VarsDeclNode):
                return self.analyze_vars_decl(node), None
            elif isinstance(node, AssignNode):
                return self.analyze_assign(node)
            elif isinstance(node, (WhileNode, DoWhileNode, ForNode, IfNode)):
                return self.analyze_conditionals(node), None
            elif isinstance(node, CallNode):
                return self.analyze_call(node)
            elif isinstance(node, FuncNode):
                return self.analyze_func_decl(node), None
            elif isinstance(node, ArrayNode):
                return self.analyze_array(node)
            elif isinstance(node, IndexNode):
                return self.analyze_index(node)
            elif isinstance(node, ExprNode):
                return self.analyze_inner(node.children[0])
            else:
                abstr_node = AbstractNode([], row=node.row, line=node.line)
                for child in node.children:
                    node_to_add, _ = self.analyze_inner(child)
                    abstr_node.ch.append(node_to_add)
                return abstr_node, None

        else:
            if isinstance(node, LiteralNode):
                v_type = self.get_type(node.value, True)
                if isinstance(v_type, String) and node.literal[0] == "'":
                    v_type = Char('char', False)
                return ConstNode(node.value, v_type, line=node.line, row=node.row), v_type
            elif isinstance(node, IdentNode):
                var = self.find_in_scope(node.scope, node.name, 'vars')
                t = self.get_type(var[0])
                return TypedNode(node.name, t, var[1], line=node.line, row=node.row), t
            else:
                return StmtListNode(), None

    def analyze_bin_op(self, node: BinOpNode) -> Tuple[AstNode, BaseType]:
        op = str(node)
        arg1_node, arg1_type = self.analyze_inner(node.arg1)
        arg2_node, arg2_type = self.analyze_inner(node.arg2)
        if op in ('&&', '&', '||', '|'):
            return self.bin_op_bool(node, arg1_node, arg2_node, arg1_type, arg2_type, op)
        else:
            return self.bin_op_all(node, arg1_node, arg2_node, arg1_type, arg2_type, op)

    def bin_op_bool(self, node, arg1_node, arg2_node, arg1_type, arg2_type, op):
        if isinstance(arg1_type, Bool) and isinstance(arg2_type, Bool) and not (arg1_type.isArray or arg2_type.isArray):
            new_node = BinOpNode(BinOp(op), arg1_node, arg2_node, line=node.line, row=node.row)
            return new_node, arg1_type
        else:
            raise AnalyzerError("Can't compare {0} and {1}".format(arg1_type, arg2_type))

    def bin_op_all(self, node: BinOpNode, arg1_node, arg2_node, arg1_type, arg2_type, op):
        if isinstance(arg2_type, Bool) or isinstance(arg1_type, Bool):
            raise AnalyzerError("Can't do binary operations({0}) with bool variables".format(op))
        if isinstance(arg1_node, ConstNode) and isinstance(arg2_node, ConstNode):
            res = eval('{0}{1}{2}'.format(arg1_node.val, op, arg2_node.val))
            v_type = self.get_type(res, True)
            return ConstNode(res, v_type, line=node.line, row=node.row), v_type
        v_type = None
        arg1_node, res1 = self.get_cast(arg1_type, arg2_type, arg1_node)
        arg2_node, res2 = self.get_cast(arg2_type, arg1_type, arg2_node)
        if res1 == -1 and res2 == -1:
            raise AnalyzerError(
                "Can't implicitly cast {0} to {1} or {1} to {0}".format(arg1_type, arg2_type))
        if (res1 == 0 or res2 == 0) or res2 == 1:
            v_type = arg1_type
        elif res1 == 1:
            v_type = arg2_type
        new_node = BinOpNode(BinOp(op), arg1_node, arg2_node, line=node.line, row=node.row)
        return (new_node, v_type) if op in ('+', '-', '*', '/') else (new_node, Bool('bool', False))

    def analyze_vars_decl(self, node: VarsDeclNode) -> AstNode:
        var_nodes = []
        v_type = self.get_type(str(node.vars_type))
        for var in node.vars_list:
            var_node, var_type = self.analyze_inner(var)
            var_node, res = self.get_cast(var_type, v_type, var_node)
            if res == -1:
                raise AnalyzerError("Can't implicitly cast {0} to {1}".format(var_type, v_type))
            var_nodes.append(var_node)
        new_node = VarsDeclNode(node.vars_type, *var_nodes, row=node.row, line=node.line)
        return new_node

    def analyze_assign(self, node: AssignNode) -> Tuple[AstNode, BaseType]:
        if node.scope.name == 'global':
            if node.is_reassignment:
                raise AnalyzerError('Cannot reassign global values')
            if isinstance(node.val, IdentNode) or len(list(self.find_node(node.val, IdentNode))) > 0:
                raise AnalyzerError('Initializer element is not a compile-time constant')

        var_node, v_type = self.analyze_inner(node.name)
        val_node, val_type = self.analyze_inner(node.val)
        val_node, res = self.get_cast(val_type, v_type, val_node)

        if res == -1:
            raise AnalyzerError("Can't implicitly cast {0} to {1}".format(val_type, v_type))

        return AssignNode(var_node, val_node), v_type

    def analyze_conditionals(self, node: Union[WhileNode, DoWhileNode, ForNode, IfNode]) -> AstNode:
        if node.__class__.__name__ in node.scope.parent.illegal_nodes:
            raise AnalyzerError('Illegal code in global scope')
        child_list = []
        if isinstance(node, ForNode) and isinstance(node.cond, StmtListNode):
            cond_node, cond_type = StmtListNode(), Bool('bool', False)
        else:
            cond_node, cond_type = self.analyze_inner(node.cond)
        if not isinstance(cond_type, Bool):
            raise AnalyzerError("Condition must be bool")

        for child in node.children:
            if node.cond != child:
                child_node, _ = self.analyze_inner(child)
                child_list.append(child_node)
            else:
                child_list.append(cond_node)
        new_node = eval(node.__class__.__name__)
        new_node = new_node(*child_list, row=node.row, line=node.line)
        return new_node

    def analyze_call(self, node: CallNode) -> Tuple[AstNode, BaseType]:
        param_list = []
        param_types = []
        func_name = node.func.name
        func_signature = self.find_in_scope(node.scope, func_name, 'funcs')
        r_type = self.get_type(func_signature['r']) if func_signature['r'] != 'void' else Void('void')
        if len(node.params) != len(func_signature['p']):
            raise AnalyzerError('{0} accepts {1} argument(s), {2} was given instead'.format(func_name,
                                                                                            len(func_signature['p']),
                                                                                            len(node.params)))
        for index, param in enumerate(node.params):
            param_node, param_type = self.analyze_inner(param)
            p_type = self.get_type(func_signature['p'][index])
            param_node, res = self.get_cast(param_type, p_type, param_node)
            if res == -1:
                raise AnalyzerError("{0} accepts {1} as argument {2}, {3} was given instead".format(func_name, p_type,
                                                                                                    index, param_type))
            param_list.append(param_node)
            param_types.append(p_type)
        func_node = TypedFuncNode(func_name, r_type, *param_types)
        new_node = CallNode(func_node, *param_list, row=node.row, line=node.line)
        return new_node, r_type

    def analyze_func_decl(self, node: FuncNode) -> AstNode:
        param_nodes = []
        stmt_nodes = []
        if node.type.name == 'void':
            r_type = Void('void')
        else:
            r_type = self.get_type(node.type.name)
        func_node = node.inner
        for param in func_node.params.vars_list:
            if isinstance(param, VarsDeclNode):
                if len(param.vars_list) != 1 or not isinstance(param.vars_list[0], IdentNode):
                    raise AnalyzerError("Wrong parameter syntax")
                param_node = self.analyze_vars_decl(param)
                param_nodes.append(param_node)

        returns = list(self.find_node(func_node.stmts, ReturnNode))
        if not (isinstance(r_type, Void) or len(returns) != 0):
            raise AnalyzerError("{0} doesn't return anything".format(func_node.name))
        for return_node in returns:
            if return_node in func_node.stmts.children:
                continue
            return_node, return_type = self.analyze_inner(return_node.expr)
            if not return_type:
                return_type = Void('void')
            return_node, res = self.get_cast(return_type, r_type, return_node)
            if res == -1:
                raise AnalyzerError("{0} should return {1}, returns {2} instead".format(func_node.name,
                                                                                        r_type, return_type))

        for stmt in func_node.stmts.children:
            stmt_node, _ = self.analyze_inner(stmt)
            stmt_nodes.append(stmt_node)

        func_node = TypedFuncDeclNode(func_node.name, node.access, r_type, stmt_nodes, param_nodes,
                                      row=node.row, line=node.line)
        return func_node

    def analyze_array(self, node: ArrayNode) -> Tuple[AstNode, BaseType]:
        if node.scope.name == 'global' and node.is_reassignment:
            raise AnalyzerError('Cannot reassign global values')
        child_nodes = []
        array_type = self.get_type(node.type.name)
        check_type = array_type.__class__(array_type.type, False)
        length_node, length_type = self.analyze_inner(node.length)
        if not isinstance(length_type, Int):
            raise AnalyzerError("Array length must be int, {0} given instead".format(length_type))
        for child in node.contained.children:
            child_node, child_type = self.analyze_inner(child)
            child_node, res = self.get_cast(child_type, check_type, child_node)
            if res == -1:
                raise AnalyzerError("Can't implicitly cast {0} to {1}".format(child_type, check_type))
            child_nodes.append(child_node)
        new_node = TypedArrayDeclNode(node.name, child_nodes, length_node, array_type,
                                      row=node.row, line=node.line)
        return new_node, array_type

    def analyze_index(self, node: IndexNode) -> Tuple[AstNode, BaseType]:
        arr_node, arr_type = self.analyze_inner(node.ident)
        if not arr_type.isArray:
            raise AnalyzerError('Indexing non-array object')
        arr_type = copy.deepcopy(arr_type)
        arr_type.isArray = False
        index_node, index_type = self.analyze_inner(node.index)
        index_node, res = self.get_cast(index_type, Int('int'), index_node)
        if res == -1:
            raise AnalyzerError("Index must be int, {0} given instead".format(index_type))
        new_node = IndexNode(arr_node, index_node, row=node.row, line=node.line)
        return new_node, arr_type

    def find_node(self, node: AstNode, query: type):
        if len(node.children) > 0:
            for child in node.children:
                if isinstance(child, query):
                    yield child
                    return
                yield from self.find_node(child, query)

    def find_in_scope(self, scope: Scope, query: str, key: str):
        try:
            result = getattr(scope, key)[query]
            return result
        except KeyError:
            if scope.parent is None:
                raise AnalyzerError('{0} with id "{1}" not found'.format(key[:-1], query))
            else:
                return self.find_in_scope(scope.parent, query, key)

    def check_in_scope(self, scope: Scope, query: str, key: str) -> bool:
        try:
            result = getattr(scope, key)[query]
            return False
        except KeyError:
            if scope.parent is None:
                return True
            else:
                return self.check_in_scope(scope.parent, query, key)

    def get_cast(self, _from: BaseType, _to: BaseType, node: AstNode) -> Tuple[AstNode, int]:
        if _from.v_type == _to.v_type and _from.isArray == _to.isArray:
            return node, 0
        if not _from.cast(_to):
            return node, -1
        cast = CastNode(node, _from, _to)
        return cast, 1

    def get_type(self, val, is_const=False) -> BaseType:
        try:
            if is_const:
                const_type = self.type_analogs[type(val)]
                return const_type(const_type.__name__.lower(), False)
            else:
                type_arr = (val, False) if val[-2:] != '[]' else (val[:-2], True)
                return eval(type_arr[0].capitalize())(*type_arr)
        except NameError:
            raise AnalyzerError("No such type as {0}".format(val))
        except TypeError:
            raise AnalyzerError("Void can only be used in functions")
