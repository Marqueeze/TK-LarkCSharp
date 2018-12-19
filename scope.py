class Scope:
    def __init__(self, parent=None, name=None):
        self.name = name
        self.parent = parent
        self.vars = {}
        self.funcs = {}
