from mel_ast import *
from scope import Scope


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
