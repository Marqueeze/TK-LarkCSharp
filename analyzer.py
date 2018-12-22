from mel_ast import *
from scope import Scope
from base_type import *


class Analyzer:
    def __init__(self):
        self.scope = Scope(name='global')
        self.scopes = []

    def form_scope(self, tree: StmtListNode):
        self.form_scope_inner(tree, self.scope, 'global')

    def form_scope_inner(self, node: AstNode, parent: Scope, s_type: str):
        scope = parent
        if isinstance(node, VarsDeclNode):
            self.vars_decl_scope(scope, str(node.vars_type), s_type, node.vars_list)

        elif isinstance(node, FuncNode):
            s_type = 'local'
            return_type = node.type.name
            node = node.inner
            parent.funcs[str(node.name)] = {'r': return_type, 'p': [str(x.children[0]) for x in node.params.vars_list]}
            scope = Scope(parent=scope, name=str(node.name))

            for param in node.params.children:
                self.vars_decl_scope(scope, str(param.vars_type), 'param', param.vars_list)

            node = node.stmts

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

        node.scope = scope

    def vars_decl_scope(self, scope: Scope, d_type, s_type, nodes: Tuple[AstNode]):
        for node in nodes:
            if isinstance(node, IdentNode):
                scope.vars[str(node.name)] = (d_type, s_type)
            elif isinstance(node, AssignNode):
                scope.vars[str(node.var)] = (d_type, s_type)
            elif isinstance(node, ArrayNode):
                scope.vars[str(node.name)] = (d_type, s_type)
        return scope

    def analyze(self, tree: AstNode):
        self.analyze_call(tree)

    def analyze_inner(self, node: AstNode, v_type=None):
        if isinstance(node, (IfNode, ForNode, WhileNode, DoWhileNode)):
            v_type = Bool(Types.Bool, False)
            returned_type = self.analyze_expr(node.cond, v_type)
            if not v_type.__dict__ == returned_type.__dict__:
                raise AssertionError("Can't implicitly cast {1} to {0}".format(v_type, returned_type))
        pass

    def analyze_call(self, node: AstNode, v_type: BaseType=None):
        if isinstance(node, CallNode):
            signature = self.find_in_scope(node.scope, node.func.name, 'funcs')
            #
            #
            # param analysis goes HERE!!!
            #
            #

        if len(node.children) > 0:
            for child in node.children:
                self.analyze_inner(child, v_type)

    def analyze_expr(self, node: ExprNode, v_type: BaseType=None) -> Union[BaseType, None]:
        return String('string', True)


    def find_in_scope(self, scope: Scope, query: str, key: str):
        try:
            result = getattr(scope, key)[query]
            return result
        except KeyError:
            if scope.parent is None:
                raise ValueError('{0} with id "{1}" not found'.format(key[:-1], query))
            else:
                self.find_in_scope(scope.parent, query, key)

