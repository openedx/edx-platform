# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import logging
import threading

try:
    from newrelic.core.infinite_tracing_pb2 import AttributeValue
except:
    AttributeValue = None

_logger = logging.getLogger(__name__)


class StreamBuffer(object):
    def __init__(self, maxlen):
        self._queue = collections.deque(maxlen=maxlen)
        self._notify = self.condition()
        self._shutdown = False
        self._seen = 0
        self._dropped = 0

    @staticmethod
    def condition(*args, **kwargs):
        return threading.Condition(*args, **kwargs)

    def shutdown(self):
        with self._notify:
            self._shutdown = True
            self._notify.notify_all()

    def put(self, item):
        with self._notify:
            if self._shutdown:
                return

            self._seen += 1

            # NOTE: dropped can be over-counted as the queue approaches
            # capacity while data is still being transmitted.
            #
            # This is because the length of the queue can be changing as it's
            # being measured.
            if len(self._queue) >= self._queue.maxlen:
                self._dropped += 1

            self._queue.append(item)
            self._notify.notify_all()

    def stats(self):
        with self._notify:
            seen, dropped = self._seen, self._dropped
            self._seen, self._dropped = 0, 0

        return seen, dropped

    def __iter__(self):
        return StreamBufferIterator(self)


class StreamBufferIterator(object):
    def __init__(self, stream_buffer):
        self.stream_buffer = stream_buffer
        self._notify = self.stream_buffer._notify
        self._shutdown = False
        self._stream = None

    def shutdown(self):
        with self._notify:
            self._shutdown = True
            self._notify.notify_all()

    def stream_closed(self):
        return self._shutdown or self.stream_buffer._shutdown or (self._stream and self._stream.done())

    def __next__(self):
        with self._notify:
            while True:
                # When a gRPC stream receives a server side disconnect (usually in the form of an OK code)
                # the item it is waiting to consume from the iterator will not be sent, and will inevitably
                # be lost. To prevent this, StopIteration is raised by shutting down the iterator and
                # notifying to allow the thread to exit. Iterators cannot be reused or race conditions may
                # occur between iterator shutdown and restart, so a new iterator must be created from the
                # streaming buffer.
                if self.stream_closed():
                    _logger.debug("gRPC stream is closed. Shutting down and refusing to iterate.")
                    if not self._shutdown:
                        self.shutdown()
                    raise StopIteration

                try:
                    return self.stream_buffer._queue.popleft()
                except IndexError:
                    pass

                if not self.stream_closed() and not self.stream_buffer._queue:
                    self._notify.wait()

    next = __next__

    def __iter__(self):
        return self


class SpanProtoAttrs(dict):
    def __init__(self, *args, **kwargs):
        super(SpanProtoAttrs, self).__init__()
        if args:
            arg = args[0]
            if len(args) > 1:
                raise TypeError("SpanProtoAttrs expected at most 1 argument, got %d", len(args))
            elif hasattr(arg, "keys"):
                for k in arg:
                    self[k] = arg[k]
            else:
                for k, v in arg:
                    self[k] = v

        for k in kwargs:
            self[k] = kwargs[k]

    def __setitem__(self, key, value):
        super(SpanProtoAttrs, self).__setitem__(key, SpanProtoAttrs.get_attribute_value(value))

    def copy(self):
        copy = SpanProtoAttrs()
        copy.update(self)
        return copy

    @staticmethod
    def get_attribute_value(value):
        if isinstance(value, bool):
            return AttributeValue(bool_value=value)
        elif isinstance(value, float):
            return AttributeValue(double_value=value)
        elif isinstance(value, int):
            return AttributeValue(int_value=value)
        else:
            return AttributeValue(string_value=str(value))
