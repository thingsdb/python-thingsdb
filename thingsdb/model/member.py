class Member:
    def __init__(self, enum_name, name, value):
        self._name = name
        self._value = value
        self._enum_name = enum_name

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return f'{self._enum_name}{{{self._name}}}'
