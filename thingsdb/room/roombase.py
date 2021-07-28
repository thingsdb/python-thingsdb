import abc
import asyncio
import logging
import functools
from typing import Union
from ..client import Client
from ..client.protocol import Proto


class RoomBase(abc.ABC):

    def __init_subclass__(cls):
        cls._event_handlers = {}

        for key, val in cls.__dict__.items():
            if not key.startswith('__') and \
                    callable(val) and hasattr(val, '_event'):
                if asyncio.iscoroutinefunction(val):
                    val = functools.partial(asyncio.ensure_future, val)
                cls._event_handlers[val._event] = val

    def __init__(
            self,
            room: Union[int, str],
            scope: str = None):
        """Initializes an emitter.

        Args:
            client (thingsdb.client.Client):
                ThingsDB Client instance.
            room (int/str):
                The room Id or ThingsDB code which returns the Id of the room.
                Examples are:
                   - 123
                   - '.my_room.id();'
            scope (str):
                Collection scope. Defaults to the scope of the client.
        """
        self._client = None
        self._id = room
        self._scope = scope

    @property
    def scope(self):
        return self._scope

    @property
    def id(self):
        return self._id if isinstance(self._id, int) else None

    async def join(self, client: Client):
        async with client._rooms_lock:
            if self._scope is None:
                self._scope = client.get_default_scope()
            self._client = client

            if isinstance(self._id, str):
                code = self._id
                id = await client.query(code, scope=self._scope)
                if not isinstance(id, int):
                    raise TypeError(
                        f'expecting ThingsDB code `{code}` to return with a '
                        f'room Id (integer value), '
                        f'but got type `{type(id).__name__}`')
                res = await client._join(id, scope=self._scope)
                if res[0] is None:
                    raise LookupError(
                        f'room with Id {id} not found; '
                        f'the room Id has been returned using the ThingsDB '
                        f'code `{code}` using scope `{self._scope}`')
                self._id = id
            else:
                assert isinstance(self._id, int)
                res = await client._join(self._id, scope=self._scope)
                if res[0] is None:
                    raise LookupError(f'room with Id {self._id} not found')

            if self._id in client._rooms:
                prev = client._rooms[self._id]
                logging.warn(
                    f'Room Id {self._id} is previously registered by {prev} '
                    f'and will be overwritten with {self}')

            client._rooms[self._id] = self
            self.on_init()

    async def leave(self):
        if not isinstance(self._id, int):
            raise TypeError(
                'room Id is not an integer; most likely `join()` has never '
                'been called')
        self._client._leave(self._id, scope=self._scope)

    def _on_event(self, pkg):
        self.__class__._EVENT_MAP[pkg.tp](self, pkg.data)

    @abc.abstractmethod
    def on_init(self) -> None:
        pass

    @abc.abstractmethod
    def on_join(self) -> None:
        pass

    @abc.abstractmethod
    def on_leave(self) -> None:
        pass

    def _on_stop(self, func):
        try:
            del self._client._rooms[self._id]
        except KeyError:
            pass
        func()

    def _call_event_handler(self, data):
        cls = self.__class__
        try:
            fun = cls._event_handlers[data['event']]
        except KeyError:
            logging.debug(
                f"No handler found for `{data['event']}` on {cls.__name__}")
        else:
            fun(self, *data['args'])

    _EVENT_MAP = {
        Proto.ON_ROOM_EVENT: _call_event_handler,
        Proto.ON_ROOM_JOIN: lambda s, _: s.on_join(),
        Proto.ON_ROOM_LEAVE: lambda s, _: s._on_stop(s.on_leave),
        Proto.ON_ROOM_DELETE: lambda s, _: s._on_stop(s.on_delete),
    }

    @staticmethod
    def event(event):
        def wrapped(fun):
            fun._event = event
            return fun

        return wrapped
