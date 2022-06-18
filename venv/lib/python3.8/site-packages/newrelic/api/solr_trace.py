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

import newrelic.api.object_wrapper
import newrelic.api.time_trace
import newrelic.core.solr_node


class SolrTrace(newrelic.api.time_trace.TimeTrace):
    def __init__(self, library, command, **kwargs):
        parent = None
        if kwargs:
            if len(kwargs) > 1:
                raise TypeError("Invalid keyword arguments:", kwargs)
            parent = kwargs["parent"]
        super(SolrTrace, self).__init__(parent)

        self.library = library
        self.command = command

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (
            self.__class__.__name__,
            id(self),
            dict(library=self.library, command=self.command),
        )

    def terminal_node(self):
        return True

    def create_node(self):
        return newrelic.core.solr_node.SolrNode(
            library=self.library,
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


class SolrTraceWrapper(object):
    def __init__(self, wrapped, library, command):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None

        newrelic.api.object_wrapper.update_wrapper(self, wrapped)

        self._nr_instance = instance
        self._nr_next_object = wrapped

        if not hasattr(self, "_nr_last_object"):
            self._nr_last_object = wrapped

        self._nr_library = library
        self._nr_command = command

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_next_object.__get__(instance, klass)
        return self.__class__((instance, descriptor), self._nr_library, self._nr_command)

    def __call__(self, *args, **kwargs):
        parent = newrelic.api.time_trace.current_trace()
        if not parent:
            return self._nr_next_object(*args, **kwargs)

        if callable(self._nr_library):
            if self._nr_instance is not None:
                library = self._nr_library(self._nr_instance, *args, **kwargs)
            else:
                library = self._nr_library(*args, **kwargs)
        else:
            library = self._nr_library

        if callable(self._nr_command):
            if self._nr_instance is not None:
                command = self._nr_command(self._nr_instance, *args, **kwargs)
            else:
                command = self._nr_command(*args, **kwargs)
        else:
            command = self._nr_command

        with SolrTrace(library, command, parent=parent):
            return self._nr_next_object(*args, **kwargs)


def solr_trace(library, command):
    def decorator(wrapped):
        return SolrTraceWrapper(wrapped, library, command)

    return decorator


def wrap_solr_trace(module, object_path, library, command):
    newrelic.api.object_wrapper.wrap_object(module, object_path, SolrTraceWrapper, (library, command))
