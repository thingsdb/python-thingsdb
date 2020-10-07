import asyncio
import logging
from .prop import Prop


def checkevent(f):
    def wrapper(self, event_id, *args):
        if self._event_id > event_id:
            logging.warning(
                f'ignore event because the current event `{self._event_id}` '
                f'is greather than the received event `{event_id}`')
            return
        self._event_id = event_id
        f(self, event_id, *args)
        self._collection._go_pending()
    return wrapper


class ThingHash:
    def __init__(self, id):
        self._id = id

    def __hash__(self):
        return self._id

    def __eq__(self, other):
        return self._id == other._id


class Thing(ThingHash):
    # When __STRICT__ is set to `True`, only properties which are defined in
    # the model class are assigned to a `Thing` instance. If `False`, all
    # properties are set, not only the ones defined by the model class.
    __STRICT__ = False

    # When __SET_ANYWAY__ is set to `True`, values which do mot match the
    # specification will be assigned to a `Thing` instance anyway and only
    # a warning will be logged. If `False`, the properties will not be set.
    __SET_ANYWAY__ = False

    # When __AS_TYPE__ is set to `True`, this class will be created in
    # thingsdb as a Type when using the `build(..)` method. If `False`, no type
    # will be created. A Collection instance will have `False` as default.
    __AS_TYPE__ = True

    _ev_handlers = dict()
    _props = dict()
    _type_name = None  # Only set when __AS_TYPE__ is True
    _visited = 0  # For build, 0=not visited, 1=new_type, 2=set_type, 3=build

    def __init__(self, collection, id: int):
        super().__init__(id)
        self._event_id = 0
        self._collection = collection
        collection._register_klass(self)
        collection._register(self)

    def __init_subclass__(cls):
        cls._ev_handlers = {}
        cls._props = {}
        items = {
            k: v for k, v in cls.__dict__.items() if not k.startswith('__')}
        for key, val in items.items():
            if isinstance(val, str):
                val = val,
            if isinstance(val, tuple):
                cls._props[key] = Prop(*val)
                delattr(cls, key)
            elif callable(val) and hasattr(val, '_ev'):
                cls._ev_handlers[val._ev] = val

        if cls.__AS_TYPE__:
            cls._type_name = getattr(cls, '__TYPE_NAME__', cls.__name__)

    def __bool__(self):
        return bool(self._event_id)

    def __repr__(self):
        return f'#{self._id}'

    def id(self):
        return self._id

    def get_collection(self):
        return self._collection

    def get_client(self):
        return self._collection._client

    def watch(self):
        collection = self._collection
        return collection._client.watch(self._id, scope=collection._scope)

    def unwatch(self):
        collection = self._collection
        return collection._client.unwatch(self._id, scope=collection._scope)

    def emit(self, event, *args):
        data = {f'd{i}': v for i, v in enumerate(args)}
        dstr = "".join((f", {k}" for k in data.keys()))

        return self._collection.query(
            f'thing(id).emit(event{dstr});',
            id=self._id,
            event=event,
            **data)

    @checkevent
    def on_init(self, event, data):
        self._job_set(data)

    @checkevent
    def on_update(self, event, jobs):
        for job_dict in jobs:
            for name, job in job_dict.items():
                jobfun = self._UPDMAP.get(name)
                if jobfun is None:
                    raise TypeError(f'unknown job `{name}` for `{self}`')
                jobfun(self, job)

    def on_delete(self):
        self._collection._things.pop(self.id())

    def on_event(self, ev, *args):
        cls = self.__class__
        fun = cls._ev_handlers.get(ev)
        if fun is None:
            logging.debug(f'no event handler for {ev} on {cls.__name__}')
            return
        fun(self, *args)

    def on_stop(self):
        logging.warning(f'stopped watching thing {self}')

    def _job_add(self, pair):
        cls = self.__class__
        (k, v), = pair.items()
        prop = cls._props.get(k)

        if not prop and cls.__STRICT__:
            return

        try:
            set_ = getattr(self, k)
        except AttributeError:
            if prop:
                logging.warning(
                    f'missing property `{k}` on `{self}` '
                    f'while the property is defined in the '
                    f'model class as `{prop.spec}`')
            return

        if not isinstance(set_, set):
            logging.warning(
                f'got a add job for property `{k}` on `{self}` '
                f'while the property is of type `{type(set_)}`')
            return

        convert = prop.nconv if prop else self._collection._conv_thing
        try:
            set_.update((convert(item) for item in v))
        except Exception as e:
            logging.warning(
                f'got a value for property `{k}` on `{self}` which '
                f'does not match `{prop.spec if prop else "thing"}` ({e})')

    def _job_del(self, k):
        prop = self.__class__._props.get(k)
        if prop:
            logging.warning(
                f'property `{k}` on `{self}` will be removed while it '
                f'is defined in the model class as `{prop.spec}`')
        try:
            delattr(self, k)
        except AttributeError:
            pass

    def _job_event(self, data):
        self.on_event(*data)

    def _job_remove(self, pair):
        cls = self.__class__
        (k, v), = pair.items()
        prop = cls._props.get(k)

        if not prop and cls.__STRICT__:
            return

        try:
            set_ = getattr(self, k)
        except AttributeError:
            if prop:
                logging.warning(
                    f'missing property `{k}` on `{self}` '
                    f'while the property is defined in the '
                    f'model class as `{prop.spec}`')
            return

        if not isinstance(set_, set):
            logging.warning(
                f'got a remove job for property `{k}` on `{self}` '
                f'while the property is of type `{type(set_)}`')
            return

        set_.difference_update((ThingHash(id) for id in v))

    def _job_set(self, pairs):
        cls = self.__class__

        for k, v in pairs.items():
            if k == '#':
                continue

            prop = cls._props.get(k)
            if prop:
                convert = prop.vconv
            elif cls.__STRICT__:
                continue
            else:
                convert = self._collection._conv_any

            try:
                v = convert(v)
            except Exception as e:
                logging.warning(
                    f'got a value for property `{k}` on `{self}` which does '
                    f'not match `{prop.spec if prop else "any"}` ({repr(e)})')
                if not cls.__SET_ANYWAY__:
                    continue
            setattr(self, k, v)

        self._collection._go_pending()

    def _job_splice(self, pair):
        cls = self.__class__
        (k, v), = pair.items()
        prop = cls._props.get(k)

        if not prop and cls.__STRICT__:
            return

        try:
            arr = getattr(self, k)
        except AttributeError:
            if prop:
                logging.warning(
                    f'missing property `{k}` on `{self}` '
                    f'while the property is defined in the '
                    f'model class as `{prop.spec}`')
            return

        if not isinstance(arr, list):
            logging.warning(
                f'got a splice job for property `{k}` on `{self}` '
                f'while the property is of type `{type(arr)}`')
            return

        index, count, *items = v
        convert = prop.nconv if prop else self._collection._conv_any
        try:
            arr[index:index+count] = (convert(item) for item in items)
        except (TypeError, ValueError) as e:
            logging.warning(
                f'got a value for property `{k}` on `{self}` '
                f'which does not match `{prop.spec if prop else "any"}` ({e})')

    def _job_del_procedure(self, data):
        delattr(self._collection, data)

    def _job_del_type(self, data):
        # we can just as well keep the type so simply ignore this event
        pass

    def _job_mod_type_add(self, data):
        self._collection._upd_type_add(data)

    def _job_mod_type_del(self, data):
        self._collection._upd_type_del(data)

    def _job_mod_type_mod(self, data):
        # we do not care about the specification so simply ignore this event
        pass

    def _job_mod_type_ren(self, data):
        self._collection._upd_type_ren(data)

    def _job_mod_type_wpo(self, data):
        # we do not care about wrap-only mode so simply ignore this event
        pass

    def _job_mod_enum_add(self, data):
        self._collection._upd_enum_add(data)

    def _job_mod_enum_del(self, data):
        self._collection._upd_enum_del(data)

    def _job_mod_enum_def(self, data):
        self._collection._upd_enum_def(data)

    def _job_mod_enum_mod(self, data):
        self._collection._upd_enum_mod(data)

    def _job_mod_enum_ren(self, data):
        self._collection._upd_enum_ren(data)

    def _job_new_procedure(self, data):
        self._collection._set_procedure(data)

    def _job_new_type(self, data):
        data['fields'] = []
        self._collection._update_type(data)

    def _job_rename_enum(self, data):
        # rename a enum type
        pass

    def _job_rename_procedure(self, data):
        self._collection._rename_procedure(data)

    def _job_rename_type(self, data):
        # we do not rename a type in python
        pass

    def _job_set_type(self, data):
        self._collection._update_type(data)

    _UPDMAP = {
        # Thing jobs
        'add': _job_add,
        'del': _job_del,
        'event': _job_event,
        'remove': _job_remove,
        'set': _job_set,
        'splice': _job_splice,

        # Collection jobs
        'del_procedure': _job_del_procedure,
        'del_type': _job_del_type,
        'mod_type_add': _job_mod_type_add,
        'mod_type_del': _job_mod_type_del,
        'mod_type_mod': _job_mod_type_mod,
        'mod_type_ren': _job_mod_type_ren,
        'mod_type_wpo': _job_mod_type_wpo,
        'mod_enum_add': _job_mod_enum_add,
        'mod_enum_def': _job_mod_enum_def,
        'mod_enum_del': _job_mod_enum_del,
        'mod_enum_mod': _job_mod_enum_mod,
        'mod_enum_ren': _job_mod_enum_ren,
        'new_procedure': _job_new_procedure,
        'new_type': _job_new_type,
        'rename_enum': _job_rename_enum,
        'rename_procedure': _job_rename_procedure,
        'rename_type': _job_rename_type,
        'set_type': _job_set_type,
    }

    @classmethod
    async def _new_type(cls, client, collection):
        if cls._visited > 0:
            return
        cls._visited += 1

        for prop in cls._props.values():
            if prop.model:
                await prop.model._new_type(client, collection)

        if not cls._type_name:
            return

        await client.query(f'''
            new_type('{cls._type_name}');
        ''', scope=collection._scope)

    @classmethod
    async def _set_type(cls, client, collection):
        if cls._visited > 1:
            return
        cls._visited += 1

        for prop in cls._props.values():
            if prop.model:
                await prop.model._set_type(client, collection)

        if not cls._type_name:
            return

        await client.query(f'''
            set_type('{cls._type_name}', {{
                {', '.join(f'{k}: "{p.spec}"' for k, p in cls._props.items())}
            }});
        ''', scope=collection._scope)


class ThingStrict(Thing):

    __STRICT__ = True
