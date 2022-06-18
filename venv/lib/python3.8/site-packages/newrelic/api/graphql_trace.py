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
from newrelic.api.transaction import current_transaction
from newrelic.common.async_wrapper import async_wrapper
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.core.graphql_node import GraphQLOperationNode, GraphQLResolverNode


class GraphQLOperationTrace(TimeTrace):
    def __init__(self, **kwargs):
        parent = None
        if kwargs:
            if len(kwargs) > 1:
                raise TypeError("Invalid keyword arguments:", kwargs)
            parent = kwargs["parent"]
        super(GraphQLOperationTrace, self).__init__(parent)

        self.operation_name = "<anonymous>"
        self.operation_type = "<unknown>"
        self.deepest_path = "<unknown>"
        self.graphql = None
        self.graphql_format = None
        self.statement = None
        self.product = "GraphQL"

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (
            self.__class__.__name__,
            id(self),
            dict(
                operation_name=self.operation_name,
                operation_type=self.operation_type,
                deepest_path=self.deepest_path,
                graphql=self.graphql,
            ),
        )

    @property
    def formatted(self):
        if not self.statement:
            return "<unknown>"

        transaction = current_transaction(active_only=False)

        # Record SQL settings
        settings = transaction.settings
        tt = settings.transaction_tracer
        self.graphql_format = tt.record_sql

        return self.statement.formatted(self.graphql_format)

    def finalize_data(self, transaction, exc=None, value=None, tb=None):
        # Add attributes
        self._add_agent_attribute("graphql.operation.type", self.operation_type)
        self._add_agent_attribute("graphql.operation.name", self.operation_name)

        # Attach formatted graphql
        limit = transaction.settings.agent_limits.sql_query_length_maximum
        self.graphql = graphql = self.formatted[:limit]
        self._add_agent_attribute("graphql.operation.query", graphql)

        return super(GraphQLOperationTrace, self).finalize_data(transaction, exc=None, value=None, tb=None)

    def create_node(self):
        return GraphQLOperationNode(
            children=self.children,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            exclusive=self.exclusive,
            guid=self.guid,
            agent_attributes=self.agent_attributes,
            user_attributes=self.user_attributes,
            operation_name=self.operation_name,
            operation_type=self.operation_type,
            deepest_path=self.deepest_path,
            graphql=self.graphql,
            product=self.product,
        )

    def set_transaction_name(self, priority=None):
        transaction = current_transaction()
        if transaction:
            name = (
                "%s/%s/%s" % (self.operation_type, self.operation_name, self.deepest_path)
                if self.deepest_path
                else "%s/%s" % (self.operation_type, self.operation_name)
            )
            transaction.set_transaction_name(name, "GraphQL", priority=priority)


def GraphQLOperationTraceWrapper(wrapped):
    def _nr_graphql_trace_wrapper_(wrapped, instance, args, kwargs):
        wrapper = async_wrapper(wrapped)
        if not wrapper:
            parent = current_trace()
            if not parent:
                return wrapped(*args, **kwargs)
        else:
            parent = None

        trace = GraphQLOperationTrace(parent=parent)

        if wrapper:  # pylint: disable=W0125,W0126
            return wrapper(wrapped, trace)(*args, **kwargs)

        with trace:
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, _nr_graphql_trace_wrapper_)


def graphql_operation_trace():
    return functools.partial(GraphQLOperationTraceWrapper)


def wrap_graphql_operation_trace(module, object_path):
    wrap_object(module, object_path, GraphQLOperationTraceWrapper)


class GraphQLResolverTrace(TimeTrace):
    def __init__(self, field_name=None, **kwargs):
        super(GraphQLResolverTrace, self).__init__(**kwargs)
        self.field_name = field_name
        self._product = None

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (self.__class__.__name__, id(self), dict(field_name=self.field_name))

    def __enter__(self):
        super(GraphQLResolverTrace, self).__enter__()
        _ = self.product  # Cache product value
        return self

    @property
    def product(self):
        if not self._product:
            # Find GraphQLOperationTrace to obtain stored product info
            parent = self  # init to self for loop start
            while parent is not None and not isinstance(parent, GraphQLOperationTrace):
                parent = getattr(parent, "parent", None)

            if parent is not None:
                self._product = getattr(parent, "product", "GraphQL")
            else:
                self._product = "GraphQL"

        return self._product

    def finalize_data(self, *args, **kwargs):
        self._add_agent_attribute("graphql.field.name", self.field_name)

        return super(GraphQLResolverTrace, self).finalize_data(*args, **kwargs)

    def create_node(self):
        return GraphQLResolverNode(
            field_name=self.field_name,
            children=self.children,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            exclusive=self.exclusive,
            guid=self.guid,
            agent_attributes=self.agent_attributes,
            user_attributes=self.user_attributes,
            product=self.product,
        )


def GraphQLResolverTraceWrapper(wrapped):
    def _nr_graphql_trace_wrapper_(wrapped, instance, args, kwargs):
        wrapper = async_wrapper(wrapped)
        if not wrapper:
            parent = current_trace()
            if not parent:
                return wrapped(*args, **kwargs)
        else:
            parent = None

        trace = GraphQLResolverTrace(parent=parent)

        if wrapper:  # pylint: disable=W0125,W0126
            return wrapper(wrapped, trace)(*args, **kwargs)

        with trace:
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, _nr_graphql_trace_wrapper_)


def graphql_resolver_trace():
    return functools.partial(GraphQLResolverTraceWrapper)


def wrap_graphql_resolver_trace(module, object_path):
    wrap_object(module, object_path, GraphQLResolverTraceWrapper)
