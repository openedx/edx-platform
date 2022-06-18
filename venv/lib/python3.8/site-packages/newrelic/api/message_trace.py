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

from newrelic.api.cat_header_mixin import CatHeaderMixin
from newrelic.api.time_trace import TimeTrace, current_trace
from newrelic.common.async_wrapper import async_wrapper
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.core.message_node import MessageNode


class MessageTrace(CatHeaderMixin, TimeTrace):

    cat_id_key = "NewRelicID"
    cat_transaction_key = "NewRelicTransaction"
    cat_appdata_key = "NewRelicAppData"
    cat_synthetics_key = "NewRelicSynthetics"

    def __init__(self, library, operation, destination_type, destination_name, params=None, **kwargs):

        parent = None
        if kwargs:
            if len(kwargs) > 1:
                raise TypeError("Invalid keyword arguments:", kwargs)
            parent = kwargs["parent"]
        super(MessageTrace, self).__init__(parent)

        self.library = library
        self.operation = operation

        self.params = params

        self.destination_type = destination_type
        self.destination_name = destination_name

    def __enter__(self):
        result = super(MessageTrace, self).__enter__()

        if result and self.transaction:
            self.library = self.transaction._intern_string(self.library)
            self.operation = self.transaction._intern_string(self.operation)

        # Only record parameters when not high security mode and only
        # when enabled in settings.
        if not (
            self.should_record_segment_params
            and self.settings
            and self.settings.message_tracer.segment_parameters_enabled
        ):
            self.params = None
        return result

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (
            self.__class__.__name__,
            id(self),
            dict(library=self.library, operation=self.operation),
        )

    def terminal_node(self):
        return True

    def create_node(self):
        return MessageNode(
            library=self.library,
            operation=self.operation,
            children=self.children,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            exclusive=self.exclusive,
            destination_name=self.destination_name,
            destination_type=self.destination_type,
            params=self.params,
            guid=self.guid,
            agent_attributes=self.agent_attributes,
            user_attributes=self.user_attributes,
        )


def MessageTraceWrapper(wrapped, library, operation, destination_type, destination_name, params={}):
    def _nr_message_trace_wrapper_(wrapped, instance, args, kwargs):
        wrapper = async_wrapper(wrapped)
        if not wrapper:
            parent = current_trace()
            if not parent:
                return wrapped(*args, **kwargs)
        else:
            parent = None

        if callable(library):
            if instance is not None:
                _library = library(instance, *args, **kwargs)
            else:
                _library = library(*args, **kwargs)
        else:
            _library = library

        if callable(operation):
            if instance is not None:
                _operation = operation(instance, *args, **kwargs)
            else:
                _operation = operation(*args, **kwargs)
        else:
            _operation = operation

        if callable(destination_type):
            if instance is not None:
                _destination_type = destination_type(instance, *args, **kwargs)
            else:
                _destination_type = destination_type(*args, **kwargs)
        else:
            _destination_type = destination_type

        if callable(destination_name):
            if instance is not None:
                _destination_name = destination_name(instance, *args, **kwargs)
            else:
                _destination_name = destination_name(*args, **kwargs)
        else:
            _destination_name = destination_name

        trace = MessageTrace(_library, _operation, _destination_type, _destination_name, params={}, parent=parent)

        if wrapper:  # pylint: disable=W0125,W0126
            return wrapper(wrapped, trace)(*args, **kwargs)

        with trace:
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, _nr_message_trace_wrapper_)


def message_trace(library, operation, destination_type, destination_name, params={}):
    return functools.partial(
        MessageTraceWrapper,
        library=library,
        operation=operation,
        destination_type=destination_type,
        destination_name=destination_name,
        params=params,
    )


def wrap_message_trace(module, object_path, library, operation, destination_type, destination_name, params={}):
    wrap_object(
        module, object_path, MessageTraceWrapper, (library, operation, destination_type, destination_name, params)
    )
