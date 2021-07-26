import abc
import asyncio
import logging
from typing import Union
from ..client import Client
from ..client.abc.events import Events


class Room(abc.ABC):

    def __init__(
            self,
            client: Client,
            room: Union[int, str],
            scope: str = None):
        """Initializes an emitter.

        Args:
            client (thingsdb.client.Client):
                ThingsDB Client instance.
            room (int/str):
                The room Id, or, ThingsDB code which returns the Id of the room.
                Examples are:
                   - 123
                   - '.my_room.id();'
            scope (str):
                Collection scope. Defaults to the scope of the client.
        """
        self._client = client
        self._id


    @abc.abstractmethod
    def on_join(self) -> None:
        """On re-connect
        Called after a re-concect is finished (including authentication)
        """
        pass

    @abc.abstractmethod
    def on_node_status(self, status: str) -> None:
        """On node status
        status: String containing a `new` node status.
                Optional values:
                    - OFFLINE
                    - CONNECTING
                    - BUILDING
                    - SHUTTING_DOWN
                    - SYNCHRONIZING
                    - AWAY
                    - AWAY_SOON
                    - READY
        """
        pass

    @abc.abstractmethod
    def on_warning(self, warn: dict) -> None:
        """On warning
        warn: a dictionary with `warn_msg` and `warn_code`. for example:

        {
            "warn_msg": "some warning message"
            "warn_code": 1
        }
        """
        pass

    @abc.abstractmethod
    def on_watch_init(self, data: dict) -> None:
        """On watch init.
        Initial data from a single thing. for example:

        {
            "#": 123,
            "name": "ThingsDB!",
            ...
        }
        """
        pass

    @abc.abstractmethod
    def on_watch_update(self, data: dict) -> None:
        """On watch update.
        Updates for a thing with ID (#). One event may contain more than one
        job. for example:

        {
            "#": 123,
            "jobs": [
                {
                    "set": {
                        "answer": 42
                    }
                }
            ]
        }
        """
        pass

    @abc.abstractmethod
    def on_watch_delete(self, data: dict) -> None:
        """On watch delete.
        The thing is removed from the collection (and garbage collected).
        for example:

        {
            "#": 123
        }
        """
        pass

    @abc.abstractmethod
    def on_watch_stop(self, data: dict) -> None:
        """On watch stop.
        The thing is not watched anymore due to either call to `unwatch()`, or
        by a unwatch request (REQ_UNWATCH). This event is *not* triggered when
        a connection to a node has been lost.

        for example:

        {
            "#": 123
        }
        """
        pass
