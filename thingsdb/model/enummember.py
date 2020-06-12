class EnumMember:

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    def __new__(cls, enum_name, name, value):
        instance = object.__new__(cls)
        instance._name = name
        instance._value = value
        instance._enum_name = enum_name
        return instance

    def __repr__(self):
        return f'{self._enum_name}{{{self._name}}}'

    def __eq__(self, other):
        return self is other or self._value == other

    def __ne__(self, other):
        return not self.__eq__(other)
