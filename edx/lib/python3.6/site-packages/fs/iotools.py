"""Compatibility tools between Python 2 and Python 3 I/O interfaces.
"""

from __future__ import print_function
from __future__ import unicode_literals

import io
import typing
from io import SEEK_SET, SEEK_CUR

from .mode import Mode

if False:  # typing.TYPE_CHECKING
    from io import RawIOBase, IOBase
    from typing import (
        Any,
        BinaryIO,
        Iterable,
        Iterator,
        IO,
        List,
        Optional,
        Text,
        Union,
    )


class RawWrapper(io.RawIOBase):
    """Convert a Python 2 style file-like object in to a IO object.
    """

    def __init__(self, f, mode=None, name=None):
        # type: (IO[bytes], Optional[Text], Optional[Text]) -> None
        self._f = f
        self.mode = mode or getattr(f, "mode", None)
        self.name = name
        super(RawWrapper, self).__init__()

    def close(self):
        # type: () -> None
        if not self.closed:
            # Close self first since it will
            # flush itself, so we can't close
            # self._f before that
            super(RawWrapper, self).close()
            self._f.close()

    def fileno(self):
        # type: () -> int
        return self._f.fileno()

    def flush(self):
        # type: () -> None
        return self._f.flush()

    def isatty(self):
        # type: () -> bool
        return self._f.isatty()

    def seek(self, offset, whence=SEEK_SET):
        # type: (int, int) -> int
        return self._f.seek(offset, whence)

    def readable(self):
        # type: () -> bool
        return getattr(self._f, "readable", lambda: Mode(self.mode).reading)()

    def writable(self):
        # type: () -> bool
        return getattr(self._f, "writable", lambda: Mode(self.mode).writing)()

    def seekable(self):
        # type: () -> bool
        try:
            return self._f.seekable()
        except AttributeError:
            try:
                self.seek(0, SEEK_CUR)
            except IOError:
                return False
            else:
                return True

    def tell(self):
        # type: () -> int
        return self._f.tell()

    def truncate(self, size=None):
        # type: (Optional[int]) -> int
        return self._f.truncate(size)

    def write(self, data):
        # type: (bytes) -> int
        count = self._f.write(data)
        return len(data) if count is None else count

    @typing.no_type_check
    def read(self, n=-1):
        # type: (int) -> bytes
        if n == -1:
            return self.readall()
        return self._f.read(n)

    def read1(self, n=-1):
        # type: (int) -> bytes
        return getattr(self._f, "read1", self.read)(n)

    @typing.no_type_check
    def readall(self):
        # type: () -> bytes
        return self._f.read()

    @typing.no_type_check
    def readinto(self, b):
        # type: (bytearray) -> int
        try:
            return self._f.readinto(b)
        except AttributeError:
            data = self._f.read(len(b))
            bytes_read = len(data)
            b[: len(data)] = data
            return bytes_read

    @typing.no_type_check
    def readinto1(self, b):
        # type: (bytearray) -> int
        try:
            return self._f.readinto1(b)
        except AttributeError:
            data = self._f.read1(len(b))
            bytes_read = len(data)
            b[: len(data)] = data
            return bytes_read

    def readline(self, limit=-1):
        # type: (int) -> bytes
        return self._f.readline(limit)

    def readlines(self, hint=-1):
        # type: (int) -> List[bytes]
        return self._f.readlines(hint)

    def writelines(self, sequence):
        # type: (Iterable[Union[bytes, bytearray]]) -> None
        return self._f.writelines(sequence)

    def __iter__(self):
        # type: () -> Iterator[bytes]
        return iter(self._f)


@typing.no_type_check
def make_stream(
    name,  # type: Text
    bin_file,  # type: RawIOBase
    mode="r",  # type: Text
    buffering=-1,  # type: int
    encoding=None,  # type: Optional[Text]
    errors=None,  # type: Optional[Text]
    newline="",  # type: Optional[Text]
    line_buffering=False,  # type: bool
    **kwargs  # type: Any
):
    # type: (...) -> IO
    """Take a Python 2.x binary file and return an IO Stream.
    """
    reading = "r" in mode
    writing = "w" in mode
    appending = "a" in mode
    binary = "b" in mode
    if "+" in mode:
        reading = True
        writing = True

    encoding = None if binary else (encoding or "utf-8")

    io_object = RawWrapper(bin_file, mode=mode, name=name)  # type: io.IOBase
    if buffering >= 0:
        if reading and writing:
            io_object = io.BufferedRandom(
                typing.cast(io.RawIOBase, io_object),
                buffering or io.DEFAULT_BUFFER_SIZE,
            )
        elif reading:
            io_object = io.BufferedReader(
                typing.cast(io.RawIOBase, io_object),
                buffering or io.DEFAULT_BUFFER_SIZE,
            )
        elif writing or appending:
            io_object = io.BufferedWriter(
                typing.cast(io.RawIOBase, io_object),
                buffering or io.DEFAULT_BUFFER_SIZE,
            )

    if not binary:
        io_object = io.TextIOWrapper(
            io_object,
            encoding=encoding,
            errors=errors,
            newline=newline,
            line_buffering=line_buffering,
        )

    return io_object


def line_iterator(readable_file, size=None):
    # type: (IO[bytes], Optional[int]) -> Iterator[bytes]
    """Iterate over the lines of a file.

    Implementation reads each char individually, which is not very
    efficient.

    Yields:
        str: a single line in the file.

    """
    read = readable_file.read
    line = []
    byte = b"1"
    if size is None or size < 0:
        while byte:
            byte = read(1)
            line.append(byte)
            if byte in b"\n":
                yield b"".join(line)
                del line[:]

    else:
        while byte and size:
            byte = read(1)
            size -= len(byte)
            line.append(byte)
            if byte in b"\n" or not size:
                yield b"".join(line)
                del line[:]
