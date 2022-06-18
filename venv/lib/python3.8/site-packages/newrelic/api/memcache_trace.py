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

import functools

from newrelic.api.time_trace import TimeTrace, current_trace
from newrelic.common.async_wrapper import async_wrapper
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.core.memcache_node import MemcacheNode


class MemcacheTrace(TimeTrace):
    def __init__(self, command, **kwargs):
        parent = None
        if kwargs:
            if len(kwargs) > 1:
                raise TypeError("Invalid keyword arguments:", kwargs)
            parent = kwargs["parent"]
        super(MemcacheTrace, self).__init__(parent)

        self.command = command

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (self.__class__.__name__, id(self), dict(command=self.command))

    def terminal_node(self):
        return True

    def create_node(self):
        return MemcacheNode(
            command=self.command,
            children=self.children,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            exclusive=self.exclusive,
            guid=self.guid,
            agent_attributes=self.agent_attributes,
            user_attributes=self.user_attributes,
        )


def MemcacheTraceWrapper(wrapped, command):
    def _nr_wrapper_memcache_trace_(wrapped, instance, args, kwargs):
        wrapper = async_wrapper(wrapped)
        if not wrapper:
            parent = current_trace()
            if not parent:
                return wrapped(*args, **kwargs)
        else:
            parent = None

        if callable(command):
            if instance is not None:
                _command = command(instance, *args, **kwargs)
            else:
                _command = command(*args, **kwargs)
        else:
            _command = command

        trace = MemcacheTrace(_command, parent=parent)

        if wrapper:  # pylint: disable=W0125,W0126
            return wrapper(wrapped, trace)(*args, **kwargs)

        with trace:
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, _nr_wrapper_memcache_trace_)


def memcache_trace(command):
    return functools.partial(MemcacheTraceWrapper, command=command)


def wrap_memcache_trace(module, object_path, command):
    wrap_object(module, object_path, MemcacheTraceWrapper, (command,))
