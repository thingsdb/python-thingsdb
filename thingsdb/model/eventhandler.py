import logging
from ..client.abc.events import Events


class EventHandler(Events):

    def __init__(self, collection):
        super().__init__()
        self._collection = collection

    def on_reconnect(self):
        self._collection.on_reconnect()

    def on_node_status(self, _status):
        pass

    def on_warning(self, warn):
        logging.warning(f'{warn["warn_msg"]} ({warn["warn_code"]})')

    def on_watch_init(self, data):
        thing_dict = data['thing']
        thing_id = thing_dict['#']
        thing = self._collection._things.get(thing_id)
        if thing is None:
            logging.debug(
                f'Cannot init #{thing_id} since the thing is not registerd '
                f'for watching by collection `{self._collection._name}`')
            return

        thing.on_init(data['event'], thing_dict)
        if thing is self._collection:
            for procedure in data['procedures']:
                thing._set_procedure(procedure)
            for enum_info in data['enums']:
                thing._update_enum(enum_info)
            for type_info in data['types']:
                thing._update_type(type_info)

    def on_watch_update(self, data):
        thing_id = data['#']
        thing = self._collection._things.get(thing_id)
        if thing is None:
            logging.debug(
                f'Cannot update #{thing_id} since the thing is not registerd '
                f'for watching by collection `{self._collection._name}`')
            return

        thing.on_update(data['event'], data['jobs'])

    def on_watch_delete(self, data):
        thing_id = data['#']
        thing = self._collection._things.get(thing_id)
        if thing is not None:
            # since weakref is used, the thing is probably already removed and
            # the code will not reach this point, unless there are references
            # left.
            thing.on_delete()

    def on_watch_stop(self, data):
        thing_id = data['#']
        thing = self._collection._things.get(thing_id)
        if thing is not None:
            thing.on_stop()
