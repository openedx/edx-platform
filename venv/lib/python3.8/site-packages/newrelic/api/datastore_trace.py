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
from newrelic.core.datastore_node import DatastoreNode


class DatastoreTrace(TimeTrace):
    """Context manager for timing datastore queries.

    :param product: The name of the vendor.
    :type product: str
    :param target: The name of the collection or table. If the name is unknown,
                   'other' should be used.
    :type target: str
    :param operation: The name of the datastore operation. This can be the
                      primitive operation type accepted by the datastore itself
                      or the name of any API function/method in the client
                      library.
    :type operation: str
    :param host: The name of the server hosting the actual datastore.
    :type host: str
    :param port_path_or_id: The value passed in can represent either the port,
                            path, or id of the datastore being connected to.
    :type port_path_or_id: str
    :param database_name: The name of database where the current query is being
                          executed.
    :type database_name: str
    :param parent: The parent trace of this trace.
    :type parent: :class:`newrelic.api.time_trace.TimeTrace`

    Usage::

        >>> import newrelic.agent
        >>> with newrelic.agent.DatastoreTrace(
        ...        product='Redis', target='other', operation='GET',
        ...        host='localhost', port_path_or_id=1234,
        ...        database_name='meow') as nr_trace:
        ...    pass

    """

    def __init__(self, product, target, operation, host=None, port_path_or_id=None, database_name=None, **kwargs):
        parent = None
        if kwargs:
            if len(kwargs) > 1:
                raise TypeError("Invalid keyword arguments:", kwargs)
            parent = kwargs["parent"]
        super(DatastoreTrace, self).__init__(parent)

        self.instance_reporting_enabled = False
        self.database_name_enabled = False

        self.product = product
        self.target = target
        self.operation = operation

        self.host = host
        self.port_path_or_id = port_path_or_id
        self.database_name = database_name

    def __enter__(self):
        result = super(DatastoreTrace, self).__enter__()
        if result and self.transaction:
            transaction = self.transaction

            self.product = transaction._intern_string(self.product)
            self.target = transaction._intern_string(self.target)
            self.operation = transaction._intern_string(self.operation)

            datastore_tracer_settings = transaction.settings.datastore_tracer
            self.instance_reporting_enabled = datastore_tracer_settings.instance_reporting.enabled
            self.database_name_enabled = datastore_tracer_settings.database_name_reporting.enabled
        return result

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (
            self.__class__.__name__,
            id(self),
            dict(product=self.product, target=self.target, operation=self.operation),
        )

    def finalize_data(self, transaction, exc=None, value=None, tb=None):
        if not self.instance_reporting_enabled:
            self.host = None
            self.port_path_or_id = None

        if not self.database_name_enabled:
            self.database_name = None

    def terminal_node(self):
        return True

    def create_node(self):
        return DatastoreNode(
            product=self.product,
            target=self.target,
            operation=self.operation,
            children=self.children,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            exclusive=self.exclusive,
            host=self.host,
            port_path_or_id=self.port_path_or_id,
            database_name=self.database_name,
            guid=self.guid,
            agent_attributes=self.agent_attributes,
            user_attributes=self.user_attributes,
        )


def DatastoreTraceWrapper(wrapped, product, target, operation):
    """Wraps a method to time datastore queries.

    :param wrapped: The function to apply the trace to.
    :type wrapped: function
    :param product: The name of the vendor.
    :type product: str or callable
    :param target: The name of the collection or table. If the name is unknown,
                   'other' should be used.
    :type target: str or callable
    :param operation: The name of the datastore operation. This can be the
                      primitive operation type accepted by the datastore itself
                      or the name of any API function/method in the client
                      library.
    :type operation: str or callable
    :rtype: :class:`newrelic.common.object_wrapper.FunctionWrapper`

    This is typically used to wrap datastore queries such as calls to Redis or
    ElasticSearch.

    Usage::

        >>> import newrelic.agent
        >>> import time
        >>> timed_sleep = newrelic.agent.DatastoreTraceWrapper(time.sleep,
        ...        'time', None, 'sleep')

    """

    def _nr_datastore_trace_wrapper_(wrapped, instance, args, kwargs):
        wrapper = async_wrapper(wrapped)
        if not wrapper:
            parent = current_trace()
            if not parent:
                return wrapped(*args, **kwargs)
        else:
            parent = None

        if callable(product):
            if instance is not None:
                _product = product(instance, *args, **kwargs)
            else:
                _product = product(*args, **kwargs)
        else:
            _product = product

        if callable(target):
            if instance is not None:
                _target = target(instance, *args, **kwargs)
            else:
                _target = target(*args, **kwargs)
        else:
            _target = target

        if callable(operation):
            if instance is not None:
                _operation = operation(instance, *args, **kwargs)
            else:
                _operation = operation(*args, **kwargs)
        else:
            _operation = operation

        trace = DatastoreTrace(_product, _target, _operation, parent=parent)

        if wrapper:  # pylint: disable=W0125,W0126
            return wrapper(wrapped, trace)(*args, **kwargs)

        with trace:
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, _nr_datastore_trace_wrapper_)


def datastore_trace(product, target, operation):
    """Decorator allows datastore query to be timed.

    :param product: The name of the vendor.
    :type product: str
    :param target: The name of the collection or table. If the name is unknown,
                   'other' should be used.
    :type target: str
    :param operation: The name of the datastore operation. This can be the
                      primitive operation type accepted by the datastore itself
                      or the name of any API function/method in the client
                      library.
    :type operation: str

    This is typically used to decorate datastore queries such as calls to Redis
    or ElasticSearch.

    Usage::

        >>> import newrelic.agent
        >>> import time
        >>> @newrelic.agent.datastore_trace('time', None, 'sleep')
        ... def timed(*args, **kwargs):
        ...     time.sleep(*args, **kwargs)

    """
    return functools.partial(DatastoreTraceWrapper, product=product, target=target, operation=operation)


def wrap_datastore_trace(module, object_path, product, target, operation):
    """Method applies custom timing to datastore query.

    :param module: Module containing the method to be instrumented.
    :type module: object
    :param object_path: The path to the location of the function.
    :type object_path: str
    :param product: The name of the vendor.
    :type product: str
    :param target: The name of the collection or table. If the name is unknown,
                   'other' should be used.
    :type target: str
    :param operation: The name of the datastore operation. This can be the
                      primitive operation type accepted by the datastore itself
                      or the name of any API function/method in the client
                      library.
    :type operation: str

    This is typically used to time database query method calls such as Redis
    GET.

    Usage::

        >>> import newrelic.agent
        >>> import time
        >>> newrelic.agent.wrap_datastore_trace(time, 'sleep', 'time', None,
        ...        'sleep')

    """
    wrap_object(module, object_path, DatastoreTraceWrapper, (product, target, operation))
