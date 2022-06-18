from newrelic.api.asgi_application import wrap_asgi_application
from newrelic.api.error_trace import ErrorTrace
from newrelic.api.graphql_trace import GraphQLOperationTrace
from newrelic.api.transaction import current_transaction
from newrelic.api.transaction_name import TransactionNameWrapper
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.core.graphql_utils import graphql_statement
from newrelic.hooks.framework_graphql import (
    framework_version as graphql_framework_version,
)
from newrelic.hooks.framework_graphql import ignore_graphql_duplicate_exception

def framework_details():
    import graphql_server
    return ("GraphQLServer", getattr(graphql_server, "__version__", None))

def bind_query(schema, params, *args, **kwargs):
    return getattr(params, "query", None)


def wrap_get_response(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if not transaction:
        return wrapped(*args, **kwargs)

    try:
        query = bind_query(*args, **kwargs)
    except TypeError:
        return wrapped(*args, **kwargs)

    framework = framework_details()
    transaction.add_framework_info(name=framework[0], version=framework[1])
    transaction.add_framework_info(name="GraphQL", version=graphql_framework_version())

    if hasattr(query, "body"):
        query = query.body

    transaction.set_transaction_name(callable_name(wrapped), "GraphQL", priority=10)

    with GraphQLOperationTrace() as trace:
        trace.product = "GraphQLServer"
        trace.statement = graphql_statement(query)
        with ErrorTrace(ignore=ignore_graphql_duplicate_exception):
            return wrapped(*args, **kwargs)

def instrument_graphqlserver(module):
    wrap_function_wrapper(module, "get_response", wrap_get_response)    
