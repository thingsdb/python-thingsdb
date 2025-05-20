import struct
import msgpack
import logging
from typing import Optional


_fail_file = ''


def set_package_fail_file(fn: Optional[str] = ''):
    """Configure a file name to dump the last failed package.

    Only the MessagePack data will be dumped in this file, not the package
    header. This is useful for debugging packages which fail to unpack.
    Note that only a single fail file can be used which is active (or not) for
    all clients.

    When empty, a failed package will not be dumped to file.
    """
    global _fail_file
    _fail_file = fn


class Package(object):

    __slots__ = ('pid', 'length', 'total', 'tp', 'checkbit', 'data')

    st_package = struct.Struct('<IHBB')

    def __init__(self, barray: bytearray) -> None:
        self.length, self.pid, self.tp, self.checkbit = \
            self.__class__.st_package.unpack_from(barray, offset=0)
        self.total = self.__class__.st_package.size + self.length
        self.data = None

    def _handle_fail_file(self, message: bytes):
        if _fail_file:
            try:
                with open(_fail_file, 'wb') as f:
                    f.write(
                        message[self.__class__.st_package.size:self.total])
            except Exception:
                logging.exception('')
            else:
                logging.warning(
                    f'Wrote the content from {self} to `{_fail_file}`')

    def extract_data_from(self, barray: bytearray) -> None:
        try:
            self.data = msgpack.unpackb(
                bytes(barray[self.__class__.st_package.size:self.total]),
                raw=False) \
                if self.length else None
        except Exception as e:
            self._handle_fail_file(bytes(barray))
            raise e
        finally:
            del barray[:self.total]

    def read_data_from(self, message: bytes) -> None:
        try:
            self.data = msgpack.unpackb(
                message[self.__class__.st_package.size:self.total],
                raw=False) \
                if self.length else None
        except Exception as e:
            self._handle_fail_file(message)
            raise e

    def __repr__(self) -> str:
        return '<id: {0.pid} size: {0.length} tp: {0.tp}>'.format(self)
