from .enummember import EnumMember

_enums_lookup = {}  # enums lookup by name


class _GetAttr(type):
    def __getitem__(cls, name):
        for k, v in cls.__dict__.items():
            if k == name:
                return v
        raise KeyError(f'no member with name `{k}`')


class Enum(metaclass=_GetAttr):

    _visited = 0  # For build, 0=not visited, 1=new_type, 2=set_type, 3=build

    def __new__(cls, *args):
        if len(args) != 1:
            return super().__new__(cls)

        value = args[0]
        for v in cls.__dict__.values():
            if isinstance(v, EnumMember) and v._value == value:
                return v
        raise ValueError(f'no member with value `{value}`')

    def __init_subclass__(cls, **kwargs):
        if issubclass(cls, EnumMember):
            return

        cls._name = getattr(cls, '__NAME__', cls.__name__)
        cls._cname = getattr(cls, '__COLLECTION_NAME__', '')
        cls._id = None
        cls._memberclass = type(f'{cls._name}Member', (EnumMember, cls), {})

        # upgrade attributes to member instances
        for k, v in cls.__dict__.items():
            if k.startswith('_'):
                continue
            setattr(cls, k, cls._memberclass(cls._name, k, v))

        # register for lookup by name
        _enums_lookup[cls._cname + cls._name] = cls

    @staticmethod
    def _update_enum(cname, enums, data, convert):
        name = data['name']
        enum = _enums_lookup.get(name, _enums_lookup.get(cname + name))
        if enum and enum._cname and enum._cname != cname:
            raise TypeError(
                f'Enum type {name} is used in more than one collection; '
                'Add __COLLECTION_NAME__ to your Enum definition to fix '
                'this error')
        cls = EnumMember if enum is None else enum._memberclass

        members = [cls(name, k, convert(v)) for k, v in data['members']]

        if enum is not None:
            enum._cname = cname
            enum._id = data['enum_id']
            for member in members:
                setattr(enum, member.name, member)

        enums[data['enum_id']] = members, enum

    @staticmethod
    def _upd_enum_add(enums, data, convert):
        members, enum = enums[data['enum_id']]
        name = members[0]._enum_name
        cls = EnumMember if enum is None else enum._memberclass

        member = cls(name, data['name'], convert(data['value']))
        members.append(member)

        if enum is not None:
            setattr(enum, member.name, member)

    @staticmethod
    def _upd_enum_del(enums, data):
        members, enum = enums[data['enum_id']]

        if enum is not None:
            member = members[data['index']]
            delattr(enum, member.name)

        try:
            # swap remove the index
            members[data['index']] = members.pop()
        except IndexError:
            pass

    @staticmethod
    def _upd_enum_def(enums, data):
        members, _ = enums[data['enum_id']]
        # swap index
        idx = data['index']
        tmp = members[idx]
        members[idx] = members[0]
        members[0] = tmp

    @staticmethod
    def _upd_enum_mod(enums, data, convert):
        members, _ = enums[data['enum_id']]
        name = members[0]._enum_name
        member = members[data['index']]
        member._value = convert(data['value'])

    @staticmethod
    def _upd_enum_ren(enums, data):
        members, enum = enums[data['enum_id']]
        member = members[data['index']]

        if enum is not None:
            delattr(enum, member.name)
            setattr(enum, data['name'], member)

        member._name = data['name']

    @classmethod
    async def _new_type(cls, client, collection):
        if cls._visited > 0:
            return
        cls._visited += 1
        members = (
            m for m in cls.__dict__.values()
            if isinstance(m, EnumMember))
        query = f'''
            set_enum('{cls._name}', {{
                {', '.join(f'{m.name}: {m.value!r}' for m in members)}
            }});
        '''
        await client.query(query, scope=collection._scope)

    @classmethod
    async def _set_type(cls, client, collection):
        pass

    @classmethod
    def id(cls):
        return cls._id

    @classmethod
    def name(cls):
        return cls._name