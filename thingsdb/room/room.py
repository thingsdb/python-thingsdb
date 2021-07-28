import abc
import asyncio
import logging
from typing import Union
from ..client import Client
from ..client.protocol import Proto
from .roombase import RoomBase


class Room(RoomBase):
    """Class Room.

    Listening to emit events can be implemented as follow:

        @Room.event('new-msg')
        def on_new_msg(self, *args):
            pass  # do something

    """

    def on_init(self) -> None:
        """On init
        Called when a room is joined. This method will be called only once,
        thus *not* after a re-connect like the `on_join(..)` method. This
        method is called *before* the `on_join(..)` method.
        """
        pass

    def on_join(self) -> None:
        """On join
        Called when a room is joined. Unlike the `on_init(..)` method,
        the `on_join(..)` method will be called again after a re-connect.
        """
        pass

    def on_leave(self) -> None:
        """On leave
        Called when a room has been left.
        """
        pass

    def on_delete(self) -> None:
        """On delete
        Called when the room is removed from ThingsDB.
        """
        pass
