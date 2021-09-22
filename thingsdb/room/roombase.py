import abc
import asyncio
import logging
import functools
from typing import Union, Optional
from ..client import Client
from ..client.protocol import Proto


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
        self._client = None
        self._id = room
        self._scope = scope
        self._wait_join = None

    @property
    def id(self):
        return self._id if isinstance(self._id, int) else None

    @property
    def scope(self):
        return self._scope

    @property
    def client(self):
        return self._client

    async def join(self, client: Client, wait: Optional[float] = 60):
        """Join a room.

        Args:
            client (thingsdb.client.Client):
                ThingsDB client instance.
            wait (float):
                Max time (in seconds) to wait for the first `on_join` call.
                If wait is set to None, the join method will not wait for
                the first `on_join` call to happen.
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
            if wait is not None:
                self._wait_join = asyncio.Future()

        if wait is not None:
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
        return self._client._emit(self._id, event, *args, scope=self._scope)

    def _on_event(self, pkg):
        self.__class__._ROOM_EVENT_MAP[pkg.tp](self, pkg.data)

    @abc.abstractmethod
    def on_init(self) -> None:
        pass

    @abc.abstractmethod
    async def on_join(self) -> None:
        pass

    @abc.abstractmethod
    def on_leave(self) -> None:
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
        loop = self.client.get_event_loop()
        if self._wait_join:
            asyncio.ensure_future(self._on_first_join(), loop=loop)
        else:
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
            logging.debug(
                f"No emit handler found for `{event}` on {cls.__name__}")
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
