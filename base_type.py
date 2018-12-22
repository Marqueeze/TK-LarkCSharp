from enum import Enum


class BaseType(object):
    def __init__(self, _type, _is_array=False):
        self.isArray = _is_array
        self.v_type = _type

    @property
    def type(self):
        return self.v_type

    def cast(self, new_type):
        return False

    def __str__(self):
        return '{0}{1}'.format(self.v_type, '[]' if self.isArray else '')


class Int(BaseType):
    def __init__(self, _type, _is_array=False):
        super().__init__("int", _is_array)

    def cast(self, new_type):
        isinstance(new_type, Double)


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
        return isinstance(new_type, String)


class Bool(BaseType):
    def __init__(self, _type, _is_array=False):
        super().__init__("bool", _is_array)


class Types(Enum):
    Int = "int"
    Double = "double"
    String = "string"
    Char = "char"
    Bool = "bool"
