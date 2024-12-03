import abc
import asyncio
import logging
from typing import Union, Optional
from ..client import Client
from ..client.protocol import Proto
from ..util.is_name import is_name


class RoomBase(abc.ABC):

    def __init_subclass__(cls):
        cls._event_handlers = {}

        for key, val in cls.__dict__.items():
            if not key.startswith('__') and \
                    callable(val) and hasattr(val, '_event'):
                cls._event_handlers[val._event] = val

    def __init__(
            self,
            room: Union[int, str],
            scope: str = None):
        """Initializes a room.

        Args:
            room (int/str):
                The room Id or ThingsDB code which returns the Id of the room.
                Examples are:
                   - 123
                   - '.my_room.id();'
            scope (str):
                Collection scope. If no scope is given, the scope will later
                be set to the default client scope once the room is joined.
        """
        self._client: Optional[Client] = None
        self._id = room
        self._scope = scope
        self._wait_join = False

    @property
    def id(self):
        return self._id if isinstance(self._id, int) else None

    @property
    def scope(self):
        return self._scope

    @property
    def client(self):
        return self._client

    async def no_join(self, client: Client):
        """Only translate the code to a room Id.
        This is useful if you wish to use the room for emitting events but
        not listening to events in this room.
        """
        async with client._rooms_lock:
            if self._scope is None:
                self._scope = client.get_default_scope()
            self._client = client

            if isinstance(self._id, str):
                if is_name(self._id):
                    id = await client.query(
                        "room(name).id();",
                        name=self._id,
                        scope=self._scope)
                else:
                    code = self._id
                    id = await client.query(code, scope=self._scope)
                    if not isinstance(id, int):
                        raise TypeError(
                            f'expecting ThingsDB code `{code}` to return with '
                            f'a room Id (integer value), '
                            f'but got type `{type(id).__name__}`')
            else:
                id = self._id
            is_room = \
                await client.query(
                    '!is_err(try(room(id)));', id=id, scope=self._scope)
            if not is_room:
                raise TypeError(f'Id `{id}` is not a room')
            self._id = id

    async def join(self, client: Client, wait: Optional[float] = 60.0):
        """Join a room.

        Args:
            client (thingsdb.client.Client):
                ThingsDB client instance.
            wait (float):
                Max time (in seconds) to wait for the first `on_join` call.
                If wait is set to `0` or `None`, the join method will not
                wait for the first `on_join` call to happen.
        """
        # Although ThingsDB guarantees to return the response on the join
        # request before the "on_join" event is being transmitted, the asyncio
        # library might still process the "on_join" data before the result is
        # set on the future. Therefore we require a lock to ensure the room
        # is created inside the dict *before* the on_join is called.
        async with client._rooms_lock:
            if self._scope is None:
                self._scope = client.get_default_scope()
            self._client = client

            if isinstance(self._id, str):
                if is_name(self._id):
                    id = await client.query(
                        "room(name).id();",
                        name=self._id,
                        scope=self._scope)
                else:
                    code = self._id
                    id = await client.query(code, scope=self._scope)
                    if not isinstance(id, int):
                        raise TypeError(
                            f'expecting ThingsDB code `{code}` to return with '
                            f'a room Id (integer value), '
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
                logging.warning(
                    f'Room Id {self._id} is previously registered by {prev} '
                    f'and will be overwritten with {self}')

            client._rooms[self._id] = self
            self.on_init()
            if wait:
                self._wait_join = asyncio.Future()

        if wait:
            # wait for the first join to finish
            await asyncio.wait_for(self._wait_join, wait)

    async def leave(self):
        """Leave a room.

        Note: If the room is not found, a LookupError will be raised.
        """
        if not isinstance(self._id, int):
            raise TypeError(
                'room Id is not an integer; most likely `join()` has never '
                'been called')
        res = await self._client._leave(self._id, scope=self._scope)
        if res[0] is None:
            raise LookupError(f'room Id {self._id} is not found (anymore)')

    def emit(self, event: str, *args) -> asyncio.Future:
        """Emit an event.

        Args:
            event (str):
                Name of the event to emit.
            *args:
                Additional argument to send with the event.

        Returns:
            asyncio.Future (None):
                Future which should be awaited. The result of the future will
                be set to `None` when successful.
        """
        if self._client is None:
            raise RuntimeError(
                'must call join(..) or no_join(..) before using emit')
        return self._client._emit(self._id, event, *args, scope=self._scope)

    def _on_event(self, pkg) -> Optional[asyncio.Task]:
        return self.__class__._ROOM_EVENT_MAP[pkg.tp](self, pkg.data)

    @abc.abstractmethod
    def on_init(self) -> None:
        pass

    @abc.abstractmethod
    async def on_join(self) -> None:
        pass

    @abc.abstractmethod
    def on_leave(self) -> None:
        pass

    @abc.abstractmethod
    def on_emit(self, event: str, *args) -> None:
        pass

    async def _on_first_join(self):
        fut = self._wait_join
        self._wait_join = None
        # Instead of using finally to set the result, we could also catch the
        # exception and choose to set the exception to the future. (And only
        # set the future result to None on success). That implementation
        # would result in getting an exception from the join() method when the
        # wait argument is used.
        try:
            await self.on_join()
        finally:
            fut.set_result(None)

    def _on_join(self, _data):
        if self._wait_join:
            # Future, the first join. Return a task so the room lock is kept
            # until the on_first_join is finished
            return asyncio.create_task(self._on_first_join())
        elif self._wait_join is None:
            # Initially a wait was set, do not handle (new) events until the
            # join is (again) finished
            return asyncio.create_task(self.on_join())
        else:
            # User has decided not to wait for the join. Thus we can asume that
            # event handlers do not depend on the on_join to be finished
            assert self._wait_join is False
            loop = self.client.get_event_loop()
            asyncio.ensure_future(self.on_join(), loop=loop)

    def _on_stop(self, func):
        try:
            del self._client._rooms[self._id]
        except KeyError:
            pass
        func()

    def _emit_handler(self, data):
        cls = self.__class__
        event = data['event']
        try:
            fun = cls._event_handlers[event]
        except KeyError:
            self.on_emit(event, *data['args'])
        else:
            fun(self, *data['args'])

    _ROOM_EVENT_MAP = {
        Proto.ON_ROOM_EMIT: _emit_handler,
        Proto.ON_ROOM_JOIN: _on_join,
        Proto.ON_ROOM_LEAVE: lambda s, _: s._on_stop(s.on_leave),
        Proto.ON_ROOM_DELETE: lambda s, _: s._on_stop(s.on_delete),
    }

    @staticmethod
    def event(event):
        def wrapped(fun):
            fun._event = event
            return fun

        return wrapped
