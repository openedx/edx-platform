"""Dummy Frame object"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from ._cffi import ffi, C

import zmq
from zmq.utils.strtypes import unicode

_content = lambda x: x.tobytes() if type(x) == memoryview else x

class Frame(object):
    _data = None
    tracker = None
    closed = False
    more = False
    buffer = None


    def __init__(self, data, track=False, copy=None, copy_threshold=None):
        try:
            memoryview(data)
        except TypeError:
            raise

        self._data = data

        if isinstance(data, unicode):
            raise TypeError("Unicode objects not allowed. Only: str/bytes, " +
                            "buffer interfaces.")

        self.more = False
        self.tracker = None
        self.closed = False
        if track:
            self.tracker = zmq._FINISHED_TRACKER

        self.buffer = memoryview(self.bytes)

    @property
    def bytes(self):
        data = _content(self._data)
        return data

    def __len__(self):
        return len(self.bytes)

    def __eq__(self, other):
        return self.bytes == _content(other)

    def __str__(self):
        if str is unicode:
            return self.bytes.decode()
        else:
            return self.bytes

    @property
    def done(self):
        return True

Message = Frame

__all__ = ['Frame', 'Message']
