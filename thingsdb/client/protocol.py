import asyncio
import logging
from typing import Any, Callable
from .package import Package
from .baseprotocol import BaseProtocol
from .baseprotocol import Proto  # noqa: F401
try:
    from .wsprotocol import ProtocolWS  # type: ignore
except (ImportError, ModuleNotFoundError):
    class ProtocolWS(BaseProtocol):
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'missing `websockets` module; '
                'please install the `websockets` module: '
                '\n\n  pip install websockets\n\n')


class Protocol(BaseProtocol, asyncio.Protocol):

    def __init__(
        self,
        on_connection_lost: Callable[[asyncio.Protocol, Exception], None],
        on_event: Callable[[Package], None],
        loop: asyncio.AbstractEventLoop | None = None
    ):
        super().__init__(on_connection_lost, on_event)
        self._buffered_data = bytearray()
        self.package = None
        self.transport = None
        self.loop = asyncio.get_running_loop() if loop is None else loop
        self.close_future: asyncio.Future[Any] | None = None

    def connection_made(self, transport):
        '''
        override asyncio.Protocol
        '''
        self.close_future = self.loop.create_future()
        self.transport = transport

    def connection_lost(self, exc) -> None:
        '''
        override asyncio.Protocol
        '''
        self.cancel_requests()
        if self.close_future:
            self.close_future.set_result(None)
            self.close_future = None
        self.transport = None
        if not isinstance(exc, Exception):
            exc = Exception(f'connection lost ({exc})')
        self._on_connection_lost(self, exc)

    def data_received(self, data: bytes) -> None:
        '''
        override asyncio.Protocol
        '''
        self._buffered_data.extend(data)
        while self._buffered_data:
            size = len(self._buffered_data)
            if self.package is None:
                if size < Package.st_package.size:
                    return None
                self.package = Package(self._buffered_data)
            if size < self.package.total:
                return None
            try:
                self.package.extract_data_from(self._buffered_data)
            except Exception:
                logging.exception('')
                # empty the byte-array to recover from this error
                logging.error(
                    f'Exception above came from package: {self.package}')
                self._buffered_data.clear()
            else:
                self._handle_package(self.package)

            self.package = None

    def _write(self, data: Any):
        if self.transport is None:
            raise ConnectionError('no connection')
        self.transport.write(data)  # type: ignore

    def close(self):
        if self.transport:
            self.transport.close()

    def is_closing(self) -> bool:
        return self.close_future is not None

    async def wait_closed(self):
        if self.close_future:
            await self.close_future

    async def close_and_wait(self):
        self.close()
        if self.close_future:
            await self.close_future

    def info(self) -> Any:
        if self.transport:
            return self.transport.get_extra_info('socket', None)

    def is_connected(self) -> bool:
        return self.transport is not None
