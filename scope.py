from mel_ast import *

class Scope:
    def __init__(self, parent=None, name=None):
        self.name = name
        self.parent = parent
        self.vars = {}
        self.funcs = {}

    @property
    def is_func_allowed(self):
        return self.name == 'global'

    @property
    def illegal_nodes(self):
        if self.name == 'global':
            return ForNode.__name__, WhileNode.__name__, IfNode.__name__, DoWhileNode.__name__
        else:
            return ()

    def __str__(self):
        return self.name
