class Scope:
    def __init__(self, parent=None, name=None):
        self.name = name
        self.parent = parent
        self.vars = {}
        self.funcs = {}

    @property
    def is_func_allowed(self):
        return True if self.name == 'global' else False

    def __str__(self):
        return self.name
