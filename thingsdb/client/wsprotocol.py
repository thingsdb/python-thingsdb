import asyncio
import logging
from ssl import SSLContext
from typing import Any, Callable
from websockets import connect
from websockets import ClientConnection
from websockets.exceptions import ConnectionClosed
from .package import Package
from .baseprotocol import BaseProtocol


WEBSOCKET_MAX_SIZE = 2**24  # default from websocket is 2**20


class ProtocolWS(BaseProtocol):
    """More a wrapper than a true protocol."""
    def __init__(
        self,
        on_connection_lost: Callable[[asyncio.Protocol, Exception], None],
        on_event: Callable[[Package], None],
    ):
        super().__init__(on_connection_lost, on_event)
        self._proto: ClientConnection | None = None
        self._is_closing = False

    async def connect(self, uri, ssl: SSLContext | None):
        assert connect, 'websockets required, please install websockets'
        self._proto = await connect(uri, ssl=ssl, max_size=WEBSOCKET_MAX_SIZE)
        asyncio.create_task(self._recv_loop())
        self._is_closing = False
        return self

    async def _recv_loop(self):
        try:
            while True:
                data: bytes = await self._proto.recv()  # type: ignore
                pkg = None
                try:
                    pkg = Package(data)
                    pkg.read_data_from(data)
                except Exception:
                    logging.exception('')
                    # empty the byte-array to recover from this error
                    if pkg:
                        logging.error(
                            f'Exception above came from package: {pkg}')
                else:
                    self._handle_package(pkg)

        except ConnectionClosed as exc:
            self.cancel_requests()
            self._proto = None  # type: ignore
            self._on_connection_lost(self, exc)  # type: ignore

    def _write(self, data: Any):
        if self._proto is None:
            raise ConnectionError('no connection')
        asyncio.create_task(self._proto.send(data))  # type: ignore

    def close(self):
        self._is_closing = True
        if self._proto:
            asyncio.create_task(self._proto.close())  # type: ignore

    def is_closing(self) -> bool:
        return self._is_closing

    async def wait_closed(self):
        if self._proto:
            await self._proto.wait_closed()  # type: ignore

    async def close_and_wait(self):
        if self._proto:
            await self._proto.close()  # type: ignore

    def info(self) -> Any:
        return self._proto.transport.get_extra_info(  # type: ignore
            'socket',
            None)

    def is_connected(self) -> bool:
        return self._proto is not None
