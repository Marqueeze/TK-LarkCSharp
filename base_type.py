class BaseType(object):
    def __init__(self, _type, _is_array=False):
        self.isArray = _is_array
        self.Type = _type

    @property
    def type(self):
        return self.Type

    def cast(self, new_type):
        return False


class Int(BaseType):
    def __init__(self, _type, _is_array=False):
        super().__init__("int", _is_array)

    def cast(self, new_type):
        if new_type is Double:
            return True
        return False


class Double(BaseType):
    def __init__(self, _type, _is_array=False):
        super().__init__("double", _is_array)


class String(BaseType):
    def __init__(self, _type, _is_array=False):
        super().__init__("string", _is_array)


class Char(BaseType):
    def __init__(self, _type, _is_array=False):
        super().__init__("char", _is_array)

    def cast(self, new_type):
        if new_type is String:
            return True
        return False


class Bool(BaseType):
    def __init__(self, _type, _is_array=False):
        super().__init__("bool", _is_array)


class Types:
    Int = "int"
    Double = "double"
    String = "string"
    Char = "char"
    Bool = "bool"
