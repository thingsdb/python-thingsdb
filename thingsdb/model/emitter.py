import asyncio
import logging
from ..client import Client
from ..client.abc.events import Events


class Emitter(Events):

    _ev_handlers = dict()

    def __init__(self, client: Client, emitter: str = '', scope: str = None):
        """Initializes an emitter.

        Args:
            client (thingsdb.client.Client):
                ThingsDB Client instance.
            emitter (str):
                Code which should point to the `thing` to watch for events.
                Defaults to an empty string which is the collection.
                Examples are:
                   - ''
                   - '.emitter'
                   - '#123'
            scope (str):
                Collection scope. Defaults to the scope of the client.
        """
        super().__init__()
        self._event_id = 0
        self._client = client
        self._thing_id = None
        self._scope = scope or client.get_scope()
        if emitter == '.':
            emitter = ''
        if emitter:
            emitter = f'{{{emitter}}}'
        self._code = \
            f'{emitter}.watch(); {emitter}.id();'
        client.add_event_handler(self)
        asyncio.ensure_future(self._watch())

    def __init_subclass__(cls):
        cls._ev_handlers = {}

        for key, val in cls.__dict__.items():
            if not key.startswith('__') and \
                    callable(val) and hasattr(val, '_ev'):
                cls._ev_handlers[val._ev] = val

    async def _watch(self):
        self._thing_id = await self._client.query(
            self._code,
            scope=self._scope)

    def on_reconnect(self):
        asyncio.ensure_future(self._watch())

    def on_node_status(self, _status):
        pass

    def on_warning(self, warn):
        logging.warning(f'{warn["warn_msg"]} ({warn["warn_code"]})')

    def on_watch_init(self, _data):
        pass

    def on_event(self, ev, *args):
        cls = self.__class__
        fun = cls._ev_handlers.get(ev)
        if fun is None:
            logging.debug(f'no event handler for {ev} on {cls.__name__}')
            return
        fun(self, *args)

    def on_watch_update(self, data):
        thing_id = data['#']
        if thing_id != self._thing_id:
            return

        event_id, jobs = data['event'], data['jobs']

        if self._event_id > event_id:
            logging.warning(
                f'ignore event because the current event `{self._event_id}` '
                f'is greather than the received event `{event_id}`')
            return
        self._event_id = event_id

        for job_dict in jobs:
            for name, job in job_dict.items():
                if name == 'event':
                    self.on_event(*job)

    def on_watch_delete(self, data):
        thing_id = data['#']
        if thing_id == self._thing_id:
            logging.debug(f'emitter with id {thing_id} is removed')
            self._client.remove_event_handler(self)

    def on_watch_stop(self, data):
        thing_id = data['#']
        if thing_id == self._thing_id:
            logging.debug(f'emitter with id {thing_id} is stopped')
            self._client.remove_event_handler(self)
