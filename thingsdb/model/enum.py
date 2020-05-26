from .member import Member

_enums_lookup = {}  # enums lookup by name

class Enum:

    _visited = 0  # For build, 0=not visited, 1=new_type, 2=set_type, 3=build

    def __init_subclass__(cls, **kwargs):
        cls._name = getattr(cls, '__NAME__', cls.__name__)
        cls._id = None

        # upgrade attributes to member instances
        for k, v in cls.__dict__.items():
            if k.startswith('_'):
                continue
            setattr(cls, k, Member(cls._name, k, v))

        # register for lookup by name
        _enums_lookup[cls._name] = cls

    @staticmethod
    def _update_enum(enums, data, convert):
        name = data['name']
        members = [Member(name, k, convert(v)) for k, v in data['members']]

        enum = _enums_lookup.get(name)
        if enum is not None:
            enum._id = data['enum_id']
            for member in members:
                setattr(enum, member.name, member)

        enums[data['enum_id']] = members

    @staticmethod
    def _upd_enum_add(enums, data, convert):
        members = enums[data['enum_id']]
        name = members[0]._enum_name
        member = Member(name, data['name'], convert(data['value']))
        members.append(member)

        enum = _enums_lookup.get(name)
        if enum is not None:
            setattr(enum, member.name, member)

    @staticmethod
    def _upd_enum_del(enums, data):
        members = enums[data['enum_id']]
        name = members[0]._enum_name

        enum = _enums_lookup.get(name)
        if enum is not None:
            member = members[data['index']]
            delattr(enum, member.name)

        try:
            # swap remove the index
            members[data['index']] = members.pop()
        except IndexError:
            pass

    @staticmethod
    def _upd_enum_mod(enums, data, convert):
        members = enums[data['enum_id']]
        name = members[0]._enum_name
        member = members[data['index']]
        member._value = convert(data['value'])

    @staticmethod
    def _upd_enum_ren(enums, data):
        members = enums[data['enum_id']]
        name = members[0]._enum_name
        member = members[data['index']]

        enum = _enums_lookup.get(name)
        if enum is not None:
            delattr(enum, member.name)
            setattr(enum, data['name'], member)

        member._name = data['name']

    @classmethod
    async def _new_type(cls, client, collection):
        if cls._visited > 0:
            return
        cls._visited += 1
        members = (m for m in cls.__dict__.values() if isinstance(m, Member))
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