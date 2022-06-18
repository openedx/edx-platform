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

from inspect import isawaitable

from newrelic.api.asgi_application import wrap_asgi_application
from newrelic.api.error_trace import ErrorTrace
from newrelic.api.graphql_trace import GraphQLOperationTrace
from newrelic.api.transaction import current_transaction
from newrelic.api.wsgi_application import wrap_wsgi_application
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.core.graphql_utils import graphql_statement
from newrelic.hooks.framework_graphql import (
    framework_version as graphql_framework_version,
)
from newrelic.hooks.framework_graphql import ignore_graphql_duplicate_exception


def framework_details():
    import ariadne

    return ("Ariadne", getattr(ariadne, "__version__", None))


def bind_graphql(schema, data, *args, **kwargs):
    return data


def wrap_graphql_sync(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if not transaction:
        return wrapped(*args, **kwargs)

    try:
        data = bind_graphql(*args, **kwargs)
    except TypeError:
        return wrapped(*args, **kwargs)

    framework = framework_details()
    transaction.add_framework_info(name=framework[0], version=framework[1])  # No version info available on ariadne
    transaction.add_framework_info(name="GraphQL", version=graphql_framework_version())

    query = data["query"]
    if hasattr(query, "body"):
        query = query.body

    transaction.set_transaction_name(callable_name(wrapped), "GraphQL", priority=10)

    with GraphQLOperationTrace() as trace:
        trace.product = "Ariadne"
        trace.statement = graphql_statement(query)
        with ErrorTrace(ignore=ignore_graphql_duplicate_exception):
            return wrapped(*args, **kwargs)


async def wrap_graphql(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if not transaction:
        result = wrapped(*args, **kwargs)
        if isawaitable(result):
            result = await result
        return result

    try:
        data = bind_graphql(*args, **kwargs)
    except TypeError:
        result = wrapped(*args, **kwargs)
        if isawaitable(result):
            result = await result
        return result

    framework = framework_details()
    transaction.add_framework_info(name=framework[0], version=framework[1])  # No version info available on ariadne
    transaction.add_framework_info(name="GraphQL", version=graphql_framework_version())

    query = data["query"]
    if hasattr(query, "body"):
        query = query.body

    transaction.set_transaction_name(callable_name(wrapped), "GraphQL", priority=10)

    with GraphQLOperationTrace() as trace:
        trace.product = "Ariadne"
        trace.statement = graphql_statement(query)
        with ErrorTrace(ignore=ignore_graphql_duplicate_exception):
            result = wrapped(*args, **kwargs)
            if isawaitable(result):
                result = await result
            return result


def instrument_ariadne_execute(module):
    if hasattr(module, "graphql"):
        wrap_function_wrapper(module, "graphql", wrap_graphql)

    if hasattr(module, "graphql_sync"):
        wrap_function_wrapper(module, "graphql_sync", wrap_graphql_sync)


def instrument_ariadne_asgi(module):
    if hasattr(module, "GraphQL"):
        wrap_asgi_application(module, "GraphQL.__call__", framework=framework_details())


def instrument_ariadne_wsgi(module):
    if hasattr(module, "GraphQL"):
        wrap_wsgi_application(module, "GraphQL.__call__", framework=framework_details())
