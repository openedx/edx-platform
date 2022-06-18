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

import logging
from collections import deque

from newrelic.api.error_trace import ErrorTrace
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.graphql_trace import GraphQLOperationTrace, GraphQLResolverTrace
from newrelic.api.time_trace import current_trace, notice_error
from newrelic.api.transaction import current_transaction, ignore_transaction
from newrelic.common.object_names import callable_name, parse_exc_info
from newrelic.common.object_wrapper import function_wrapper, wrap_function_wrapper
from newrelic.core.graphql_utils import graphql_statement

_logger = logging.getLogger(__name__)


GRAPHQL_IGNORED_FIELDS = frozenset(("id", "__typename"))
GRAPHQL_INTROSPECTION_FIELDS = frozenset(("__schema", "__type"))
VERSION = None


def framework_version():
    """Framework version string."""
    global VERSION
    if VERSION is None:
        from graphql import __version__ as version

        VERSION = version

    return VERSION


def graphql_version():
    """Minor version tuple."""
    version = framework_version()

    # Take first two values in version to avoid ValueErrors with pre-releases (ex: 3.2.0a0)
    return tuple(int(v) for v in version.split(".")[:2])


def ignore_graphql_duplicate_exception(exc, val, tb):
    from graphql.error import GraphQLError

    if isinstance(val, GraphQLError):
        transaction = current_transaction()

        # Check that we have not recorded this exception
        # previously for this transaction due to multiple
        # error traces triggering. This happens if an exception
        # is reraised by GraphQL as a new GraphQLError type
        # after the original exception has already been recorded.

        if transaction and hasattr(val, "original_error"):
            while hasattr(val, "original_error"):
                # Unpack lowest level original error
                val = val.original_error

            _, _, fullnames, message = parse_exc_info((None, val, None))
            fullname = fullnames[0]
            for error in transaction._errors:
                if error.type == fullname and error.message == message:
                    return True

    return None  # Follow original exception matching rules


def wrap_executor_context_init(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)

    # Executors are arbitrary and swappable, but expose the same execute api
    executor = getattr(instance, "executor", None)
    if executor is not None:
        if hasattr(executor, "execute"):
            executor.execute = wrap_executor_execute(executor.execute)

    if hasattr(instance, "field_resolver"):
        if not hasattr(instance.field_resolver, "_nr_wrapped"):
            instance.field_resolver = wrap_resolver(instance.field_resolver)
            instance.field_resolver._nr_wrapped = True

    return result


def bind_operation_v3(operation, root_value):
    return operation


def bind_operation_v2(exe_context, operation, root_value):
    return operation


def wrap_execute_operation(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    trace = current_trace()

    if not transaction:
        return wrapped(*args, **kwargs)

    if not isinstance(trace, GraphQLOperationTrace):
        _logger.warning(
            "Runtime instrumentation warning. GraphQL operation found without active GraphQLOperationTrace."
        )
        return wrapped(*args, **kwargs)

    try:
        operation = bind_operation_v3(*args, **kwargs)
    except TypeError:
        try:
            operation = bind_operation_v2(*args, **kwargs)
        except TypeError:
            return wrapped(*args, **kwargs)

    if graphql_version() < (3, 0):
        execution_context = args[0]
    else:
        execution_context = instance

    trace.operation_name = get_node_value(operation, "name") or "<anonymous>"

    trace.operation_type = get_node_value(operation, "operation", "name").lower() or "<unknown>"

    if operation.selection_set is not None:
        fields = operation.selection_set.selections
        # Ignore transactions for introspection queries
        for field in fields:
            if get_node_value(field, "name") in GRAPHQL_INTROSPECTION_FIELDS:
                ignore_transaction()

        fragments = execution_context.fragments
        trace.deepest_path = ".".join(traverse_deepest_unique_path(fields, fragments)) or ""

    transaction.set_transaction_name(callable_name(wrapped), "GraphQL", priority=11)
    result = wrapped(*args, **kwargs)
    if not execution_context.errors:
        if hasattr(trace, "set_transaction_name"):
            # Operation trace sets transaction name
            trace.set_transaction_name(priority=14)

    return result


def get_node_value(field, attr, subattr="value"):
    field_name = getattr(field, attr, None)
    if hasattr(field_name, subattr):
        field_name = getattr(field_name, subattr)
    return field_name


def is_fragment_spread_node(field):
    # Resolve version specific imports
    try:
        from graphql.language.ast import FragmentSpread
    except ImportError:
        from graphql import FragmentSpreadNode as FragmentSpread

    return isinstance(field, FragmentSpread)


def is_fragment(field):
    # Resolve version specific imports
    try:
        from graphql.language.ast import FragmentSpread, InlineFragment
    except ImportError:
        from graphql import FragmentSpreadNode as FragmentSpread
        from graphql import InlineFragmentNode as InlineFragment

    _fragment_types = (InlineFragment, FragmentSpread)

    return isinstance(field, _fragment_types)


def is_named_fragment(field):
    # Resolve version specific imports
    try:
        from graphql.language.ast import NamedType
    except ImportError:
        from graphql import NamedTypeNode as NamedType

    return (
        is_fragment(field)
        and getattr(field, "type_condition", None) is not None
        and isinstance(field.type_condition, NamedType)
    )


def filter_ignored_fields(fields):
    filtered_fields = [f for f in fields if get_node_value(f, "name") not in GRAPHQL_IGNORED_FIELDS]
    return filtered_fields


def traverse_deepest_unique_path(fields, fragments):
    deepest_path = deque()
    while fields is not None and len(fields) > 0:
        fields = filter_ignored_fields(fields)
        if len(fields) != 1:  # Either selections is empty, or non-unique
            return deepest_path
        field = fields[0]
        field_name = get_node_value(field, "name")
        fragment_selection_set = []

        if is_named_fragment(field):
            name = get_node_value(field.type_condition, "name")
            if name:
                deepest_path.append("%s<%s>" % (deepest_path.pop(), name))

        elif is_fragment(field):
            if len(list(fragments.values())) != 1:
                return deepest_path

            # list(fragments.values())[0] 's index is OK because the previous line
            # ensures that there is only one field in the list
            full_fragment_selection_set = list(fragments.values())[0].selection_set.selections
            fragment_selection_set = filter_ignored_fields(full_fragment_selection_set)

            if len(fragment_selection_set) != 1:
                return deepest_path
            else:
                fragment_field_name = get_node_value(fragment_selection_set[0], "name")
                deepest_path.append(fragment_field_name)

        else:
            if field_name:
                deepest_path.append(field_name)

        if is_fragment_spread_node(field):
            field = fragment_selection_set[0]
        if field.selection_set is None:
            break
        else:
            fields = field.selection_set.selections

    return deepest_path


def bind_get_middleware_resolvers(middlewares):
    return middlewares


def wrap_get_middleware_resolvers(wrapped, instance, args, kwargs):
    try:
        middlewares = bind_get_middleware_resolvers(*args, **kwargs)
    except TypeError:
        return wrapped(*args, **kwargs)

    middlewares = [wrap_middleware(m) if not hasattr(m, "_nr_wrapped") else m for m in middlewares]
    for m in middlewares:
        m._nr_wrapped = True

    return wrapped(middlewares)


@function_wrapper
def wrap_middleware(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)
    transaction.set_transaction_name(name, "GraphQL", priority=12)
    with FunctionTrace(name):
        with ErrorTrace(ignore=ignore_graphql_duplicate_exception):
            return wrapped(*args, **kwargs)


def bind_get_field_resolver(field_resolver):
    return field_resolver


def wrap_get_field_resolver(wrapped, instance, args, kwargs):
    try:
        resolver = bind_get_field_resolver(*args, **kwargs)
    except TypeError:
        return wrapped(*args, **kwargs)

    if not hasattr(resolver, "_nr_wrapped"):
        resolver = wrap_resolver(resolver)
        resolver._nr_wrapped = True

    return wrapped(resolver)


def wrap_get_field_def(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)

    if hasattr(result, "resolve"):
        if not hasattr(result.resolve, "_nr_wrapped"):
            result.resolve = wrap_resolver(result.resolve)
            result.resolve._nr_wrapped = True

    return result


@function_wrapper
def wrap_executor_execute(wrapped, instance, args, kwargs):
    # args[0] is the resolver function, or the top of the middleware chain
    args = list(args)
    if callable(args[0]):
        if not hasattr(args[0], "_nr_wrapped"):
            args[0] = wrap_resolver(args[0])
            args[0]._nr_wrapped = True
    return wrapped(*args, **kwargs)


@function_wrapper
def wrap_resolver(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction is None:
        return wrapped(*args, **kwargs)

    transaction.set_transaction_name(callable_name(wrapped), "GraphQL", priority=13)

    with ErrorTrace(ignore=ignore_graphql_duplicate_exception):
        return wrapped(*args, **kwargs)


def wrap_error_handler(wrapped, instance, args, kwargs):
    notice_error(ignore=ignore_graphql_duplicate_exception)
    return wrapped(*args, **kwargs)


def wrap_validate(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction is None:
        return wrapped(*args, **kwargs)

    transaction.set_transaction_name(callable_name(wrapped), "GraphQL", priority=10)

    # Run and collect errors
    errors = wrapped(*args, **kwargs)

    # Raise errors and immediately catch them so we can record them
    for error in errors:
        try:
            raise error
        except:
            notice_error(ignore=ignore_graphql_duplicate_exception)

    return errors


def wrap_parse(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction is None:
        return wrapped(*args, **kwargs)

    transaction.set_transaction_name(callable_name(wrapped), "GraphQL", priority=10)
    with ErrorTrace(ignore=ignore_graphql_duplicate_exception):
        return wrapped(*args, **kwargs)


def bind_resolve_field_v3(parent_type, source, field_nodes, path):
    return parent_type, field_nodes, path


def bind_resolve_field_v2(exe_context, parent_type, source, field_asts, parent_info, field_path):
    return parent_type, field_asts, field_path


def wrap_resolve_field(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction is None:
        return wrapped(*args, **kwargs)

    if graphql_version() < (3, 0):
        bind_resolve_field = bind_resolve_field_v2
    else:
        bind_resolve_field = bind_resolve_field_v3

    try:
        parent_type, field_asts, field_path = bind_resolve_field(*args, **kwargs)
    except TypeError:
        return wrapped(*args, **kwargs)

    field_name = field_asts[0].name.value
    field_def = parent_type.fields.get(field_name)
    field_return_type = str(field_def.type) if field_def else "<unknown>"

    with GraphQLResolverTrace(field_name) as trace:
        with ErrorTrace(ignore=ignore_graphql_duplicate_exception):
            trace._add_agent_attribute("graphql.field.parentType", parent_type.name)
            trace._add_agent_attribute("graphql.field.returnType", field_return_type)

            if isinstance(field_path, list):
                trace._add_agent_attribute("graphql.field.path", field_path[0])
            else:
                trace._add_agent_attribute("graphql.field.path", field_path.key)

            return wrapped(*args, **kwargs)


def bind_graphql_impl_query(schema, source, *args, **kwargs):
    return schema, source


def bind_execute_graphql_query(
    schema,
    request_string="",
    root=None,
    context=None,
    variables=None,
    operation_name=None,
    middleware=None,
    backend=None,
    **execute_options
):
    return schema, request_string


def wrap_graphql_impl(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if not transaction:
        return wrapped(*args, **kwargs)

    transaction.add_framework_info(name="GraphQL", version=framework_version())
    if graphql_version() < (3, 0):
        bind_query = bind_execute_graphql_query
    else:
        bind_query = bind_graphql_impl_query

    try:
        schema, query = bind_query(*args, **kwargs)
    except TypeError:
        return wrapped(*args, **kwargs)

    if hasattr(query, "body"):
        query = query.body

    transaction.set_transaction_name(callable_name(wrapped), "GraphQL", priority=10)

    with GraphQLOperationTrace() as trace:
        trace.statement = graphql_statement(query)

        # Handle Schemas created from frameworks
        if hasattr(schema, "_nr_framework"):
            framework = schema._nr_framework
            trace.product = framework[0]
            transaction.add_framework_info(name=framework[0], version=framework[1])

        with ErrorTrace(ignore=ignore_graphql_duplicate_exception):
            result = wrapped(*args, **kwargs)
            return result


def instrument_graphql_execute(module):
    if hasattr(module, "get_field_def"):
        wrap_function_wrapper(module, "get_field_def", wrap_get_field_def)
    if hasattr(module, "ExecutionContext"):
        wrap_function_wrapper(module, "ExecutionContext.__init__", wrap_executor_context_init)

        if hasattr(module.ExecutionContext, "resolve_field"):
            wrap_function_wrapper(module, "ExecutionContext.resolve_field", wrap_resolve_field)
        elif hasattr(module.ExecutionContext, "execute_field"):
            wrap_function_wrapper(module, "ExecutionContext.execute_field", wrap_resolve_field)

        if hasattr(module.ExecutionContext, "execute_operation"):
            wrap_function_wrapper(module, "ExecutionContext.execute_operation", wrap_execute_operation)

    if hasattr(module, "resolve_field"):
        wrap_function_wrapper(module, "resolve_field", wrap_resolve_field)

    if hasattr(module, "execute_operation"):
        wrap_function_wrapper(module, "execute_operation", wrap_execute_operation)


def instrument_graphql_execution_utils(module):
    if hasattr(module, "ExecutionContext"):
        wrap_function_wrapper(module, "ExecutionContext.__init__", wrap_executor_context_init)


def instrument_graphql_execution_middleware(module):
    if hasattr(module, "get_middleware_resolvers"):
        wrap_function_wrapper(module, "get_middleware_resolvers", wrap_get_middleware_resolvers)
    if hasattr(module, "MiddlewareManager"):
        wrap_function_wrapper(module, "MiddlewareManager.get_field_resolver", wrap_get_field_resolver)


def instrument_graphql_error_located_error(module):
    if hasattr(module, "located_error"):
        wrap_function_wrapper(module, "located_error", wrap_error_handler)


def instrument_graphql_validate(module):
    wrap_function_wrapper(module, "validate", wrap_validate)


def instrument_graphql(module):
    if hasattr(module, "graphql_impl"):
        wrap_function_wrapper(module, "graphql_impl", wrap_graphql_impl)
    if hasattr(module, "execute_graphql"):
        wrap_function_wrapper(module, "execute_graphql", wrap_graphql_impl)


def instrument_graphql_parser(module):
    wrap_function_wrapper(module, "parse", wrap_parse)
