import enum
import asyncio
import logging
import msgpack
from abc import abstractmethod
from typing import Any, Callable
from .package import Package
from ..exceptions import AssertionError
from ..exceptions import AuthError
from ..exceptions import BadDataError
from ..exceptions import CancelledError
from ..exceptions import CustomError
from ..exceptions import ForbiddenError
from ..exceptions import InternalError
from ..exceptions import LookupError
from ..exceptions import MaxQuotaError
from ..exceptions import MemoryError
from ..exceptions import NodeError
from ..exceptions import NumArgumentsError
from ..exceptions import OperationError
from ..exceptions import OverflowError
from ..exceptions import RequestCancelError
from ..exceptions import RequestTimeoutError
from ..exceptions import ResultTooLargeError
from ..exceptions import SyntaxError
from ..exceptions import TypeError
from ..exceptions import ValueError
from ..exceptions import WriteUVError
from ..exceptions import ZeroDivisionError


class Proto(enum.IntEnum):
    # Events
    ON_NODE_STATUS = 0x00
    ON_WARN = 0x05
    ON_ROOM_JOIN = 0x06
    ON_ROOM_LEAVE = 0x07
    ON_ROOM_EMIT = 0x08
    ON_ROOM_DELETE = 0x09

    # Responses
    RES_PING = 0x10
    RES_OK = 0x11
    RES_DATA = 0x12
    RES_ERROR = 0x13

    # Requests (initiated by the client)
    REQ_PING = 0x20
    REQ_AUTH = 0x21
    REQ_QUERY = 0x22
    REQ_RUN = 0x25
    REQ_JOIN = 0x26
    REQ_LEAVE = 0x27
    REQ_EMIT = 0x28
    REQ_EMIT_PEER = 0x29


class Err(enum.IntEnum):
    """ThingsDB error codes."""

    # ThingsDB build-in errors
    EX_CANCELLED = -64
    EX_OPERATION_ERROR = -63
    EX_NUM_ARGUMENTS = -62
    EX_TYPE_ERROR = -61
    EX_VALUE_ERROR = -60
    EX_OVERFLOW = -59
    EX_ZERO_DIV = -58
    EX_MAX_QUOTA = -57
    EX_AUTH_ERROR = -56
    EX_FORBIDDEN = -55
    EX_LOOKUP_ERROR = -54
    EX_BAD_DATA = -53
    EX_SYNTAX_ERROR = -52
    EX_NODE_ERROR = -51
    EX_ASSERT_ERROR = -50

    # ThingsDB internal errors
    EX_TOO_LARGE_X = -6
    EX_REQUEST_TIMEOUT = -5
    EX_REQUEST_CANCEL = -4
    EX_WRITE_UV = -3
    EX_MEMORY = -2
    EX_INTERNAL = -1


_ERRMAP = {
    Err.EX_CANCELLED: CancelledError,
    Err.EX_OPERATION_ERROR: OperationError,
    Err.EX_NUM_ARGUMENTS: NumArgumentsError,
    Err.EX_TYPE_ERROR: TypeError,
    Err.EX_VALUE_ERROR: ValueError,
    Err.EX_OVERFLOW: OverflowError,
    Err.EX_ZERO_DIV: ZeroDivisionError,
    Err.EX_MAX_QUOTA: MaxQuotaError,
    Err.EX_AUTH_ERROR: AuthError,
    Err.EX_FORBIDDEN: ForbiddenError,
    Err.EX_LOOKUP_ERROR: LookupError,
    Err.EX_BAD_DATA: BadDataError,
    Err.EX_SYNTAX_ERROR: SyntaxError,
    Err.EX_NODE_ERROR: NodeError,
    Err.EX_ASSERT_ERROR: AssertionError,
    Err.EX_TOO_LARGE_X: ResultTooLargeError,
    Err.EX_REQUEST_TIMEOUT: RequestTimeoutError,
    Err.EX_REQUEST_CANCEL: RequestCancelError,
    Err.EX_WRITE_UV: WriteUVError,
    Err.EX_MEMORY: MemoryError,
    Err.EX_INTERNAL: InternalError,
}

_PROTO_RESPONSE_MAP = {
    Proto.RES_PING: lambda f, d: f.set_result(None),
    Proto.RES_OK: lambda f, d: f.set_result(None),
    Proto.RES_DATA: lambda f, d: f.set_result(d),
    Proto.RES_ERROR: lambda f, d: f.set_exception(_ERRMAP.get(
        d['error_code'],
        CustomError)(errdata=d)),
}

_PROTO_EVENTS = (
    Proto.ON_NODE_STATUS,
    Proto.ON_WARN,
    Proto.ON_ROOM_JOIN,
    Proto.ON_ROOM_LEAVE,
    Proto.ON_ROOM_EMIT,
    Proto.ON_ROOM_DELETE,
)


def proto_unknown(f, d):
    f.set_exception(TypeError('unknown package type received ({})'.format(d)))


class BaseProtocol:
    def __init__(
            self,
            on_connection_lost: Callable[[asyncio.Protocol, Exception], None],
            on_event: Callable[[Package], None],):
        self._requests = {}
        self._pid = 0
        self._on_connection_lost = on_connection_lost
        self._on_event = on_event

    async def _timer(self, pid: int, timeout: int) -> None:
        await asyncio.sleep(timeout)
        try:
            future, task = self._requests.pop(pid)
        except KeyError:
            logging.error(f'Timed out package Id not found: {pid}')
            return None

        future.set_exception(TimeoutError(
            f'request timed out on package Id {pid}'))

    def _on_response(self, pkg: Package) -> None:
        try:
            future, task = self._requests.pop(pkg.pid)
        except KeyError:
            logging.error(f'Received package id not found: {pkg.pid}')
            return None

        # cancel the timeout task
        if task is not None:
            task.cancel()

        if future.cancelled():
            return

        _PROTO_RESPONSE_MAP.get(pkg.tp, proto_unknown)(future, pkg.data)

    def _handle_package(self, pkg: Package):
        tp = pkg.tp
        if tp in _PROTO_RESPONSE_MAP:
            self._on_response(pkg)
        elif tp in _PROTO_EVENTS:
            try:
                self._on_event(pkg)
            except Exception:
                logging.exception('')
        else:
            logging.error(f'Unsupported package type received: {tp}')

    def write(
            self,
            tp: Proto,
            data: Any = None,
            is_bin: bool = False,
            timeout: int | None = None
    ) -> asyncio.Future[Any]:
        """Write data to ThingsDB.
        This will create a new PID and returns a Future which will be
        set when a response is received from ThingsDB, or time-out is reached.
        """
        self._pid += 1
        self._pid %= 0x10000  # pid is handled as uint16_t

        data = data if is_bin else b'' if data is None else \
            msgpack.packb(data, use_bin_type=True)

        header = Package.st_package.pack(
            len(data),
            self._pid,
            tp,
            tp ^ 0xff)

        self._write(header + data)

        task = asyncio.ensure_future(
            self._timer(self._pid, timeout)) if timeout else None

        future = asyncio.Future()
        self._requests[self._pid] = (future, task)
        return future

    def cancel_requests(self):
        if self._requests:
            logging.error(
                f'Canceling {len(self._requests)} requests '
                'due to a lost connection'
            )
            while self._requests:
                _key, (future, task) = self._requests.popitem()
                if task is not None:
                    task.cancel()
                if not future.cancelled():
                    future.cancel()

    @abstractmethod
    def _write(self, data: Any):
        ...

    @abstractmethod
    def close(self):
        ...

    @abstractmethod
    def is_closing(self) -> bool:
        ...

    @abstractmethod
    async def wait_closed(self):
        ...

    @abstractmethod
    async def close_and_wait(self):
        ...
