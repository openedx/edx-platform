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

from newrelic.api.asgi_application import wrap_asgi_application
from newrelic.api.background_task import BackgroundTaskWrapper
from newrelic.api.function_trace import FunctionTraceWrapper
from newrelic.api.time_trace import current_trace, notice_error
from newrelic.api.transaction import current_transaction
from newrelic.common.coroutine import is_coroutine_function
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (
    FunctionWrapper,
    function_wrapper,
    wrap_function_wrapper,
)
from newrelic.core.context import ContextOf, context_wrapper


def framework_details():
    import starlette

    return ("Starlette", getattr(starlette, "__version__", None))


def bind_request(request, *args, **kwargs):
    return request


def bind_exc(request, exc, *args, **kwargs):
    return exc


@function_wrapper
def route_naming_wrapper(wrapped, instance, args, kwargs):

    with ContextOf(request=bind_request(*args, **kwargs)):
        transaction = current_transaction()
        if transaction:
            transaction.set_transaction_name(callable_name(wrapped), priority=2)
        return wrapped(*args, **kwargs)


def bind_endpoint(path, endpoint, *args, **kwargs):
    return path, endpoint, args, kwargs


def bind_add_exception_handler(exc_class_or_status_code, handler, *args, **kwargs):
    return exc_class_or_status_code, handler, args, kwargs


def wrap_route(wrapped, instance, args, kwargs):
    path, endpoint, args, kwargs = bind_endpoint(*args, **kwargs)
    endpoint = route_naming_wrapper(FunctionTraceWrapper(endpoint))
    return wrapped(path, endpoint, *args, **kwargs)


def wrap_request(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    instance._nr_trace = current_trace()

    return result


def wrap_background_method(wrapped, instance, args, kwargs):
    func = getattr(instance, "func", None)
    if func:
        instance.func = wrap_background_task(func)
    return wrapped(*args, **kwargs)


@function_wrapper
def wrap_background_task(wrapped, instance, args, kwargs):
    transaction = current_transaction(active_only=False)
    if not transaction:
        return BackgroundTaskWrapper(wrapped)(*args, **kwargs)
    else:
        return FunctionTraceWrapper(wrapped)(*args, **kwargs)


async def middleware_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction:
        transaction.set_transaction_name(callable_name(wrapped), priority=1)

    dispatch_func = getattr(wrapped, "dispatch_func", None)
    name = dispatch_func and callable_name(dispatch_func)

    return await FunctionTraceWrapper(wrapped, name=name)(*args, **kwargs)


@function_wrapper
def wrap_middleware(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    return FunctionWrapper(result, middleware_wrapper)


def bind_middleware(middleware_class, *args, **kwargs):
    return middleware_class, args, kwargs


def wrap_add_middleware(wrapped, instance, args, kwargs):
    middleware, args, kwargs = bind_middleware(*args, **kwargs)
    return wrapped(wrap_middleware(middleware), *args, **kwargs)


def bind_middleware_starlette(debug=False, routes=None, middleware=None, *args, **kwargs):  # pylint: disable=W1113
    return middleware


def wrap_starlette(wrapped, instance, args, kwargs):
    middlewares = bind_middleware_starlette(*args, **kwargs)
    if middlewares:
        for middleware in middlewares:  # pylint: disable=E1133
            cls = getattr(middleware, "cls", None)
            if cls and not hasattr(cls, "__wrapped__"):
                middleware.cls = wrap_middleware(cls)

    return wrapped(*args, **kwargs)


def status_code(response):
    code = getattr(response, "status_code", None)

    def _status_code(exc, value, tb):
        return code

    return _status_code


def record_response_error(response, value):
    exc = getattr(value, "__class__", None)
    tb = getattr(value, "__traceback__", None)

    notice_error((exc, value, tb), status_code=status_code(response))


async def wrap_exception_handler_async(coro, exc):
    response = await coro
    record_response_error(response, exc)
    return response


def wrap_exception_handler(wrapped, instance, args, kwargs):
    if is_coroutine_function(wrapped):
        return wrap_exception_handler_async(FunctionTraceWrapper(wrapped)(*args, **kwargs), bind_exc(*args, **kwargs))
    else:
        with ContextOf(request=bind_request(*args, **kwargs)):
            response = FunctionTraceWrapper(wrapped)(*args, **kwargs)
            record_response_error(response, bind_exc(*args, **kwargs))
            return response


def wrap_server_error_handler(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    handler = getattr(instance, "handler", None)
    if handler:
        instance.handler = FunctionWrapper(handler, wrap_exception_handler)
    return result


def wrap_add_exception_handler(wrapped, instance, args, kwargs):
    exc_class_or_status_code, handler, args, kwargs = bind_add_exception_handler(*args, **kwargs)
    handler = FunctionWrapper(handler, wrap_exception_handler)
    return wrapped(exc_class_or_status_code, handler, *args, **kwargs)


def error_middleware_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction:
        transaction.set_transaction_name(callable_name(wrapped), priority=1)

    return FunctionTraceWrapper(wrapped)(*args, **kwargs)


def bind_run_in_threadpool(func, *args, **kwargs):
    return func, args, kwargs


async def wrap_run_in_threadpool(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    trace = current_trace()

    if not transaction or not trace:
        return await wrapped(*args, **kwargs)

    func, args, kwargs = bind_run_in_threadpool(*args, **kwargs)
    func = context_wrapper(func, trace)

    return await wrapped(func, *args, **kwargs)


def instrument_starlette_applications(module):
    framework = framework_details()
    version_info = tuple(int(v) for v in framework[1].split(".", 3)[:3])
    wrap_asgi_application(module, "Starlette.__call__", framework=framework)
    wrap_function_wrapper(module, "Starlette.add_middleware", wrap_add_middleware)

    if version_info >= (0, 12, 13):
        wrap_function_wrapper(module, "Starlette.__init__", wrap_starlette)


def instrument_starlette_routing(module):
    wrap_function_wrapper(module, "Route.__init__", wrap_route)


def instrument_starlette_requests(module):
    wrap_function_wrapper(module, "Request.__init__", wrap_request)


def instrument_starlette_middleware_errors(module):
    wrap_function_wrapper(module, "ServerErrorMiddleware.__call__", error_middleware_wrapper)

    wrap_function_wrapper(module, "ServerErrorMiddleware.__init__", wrap_server_error_handler)

    wrap_function_wrapper(module, "ServerErrorMiddleware.error_response", wrap_exception_handler)

    wrap_function_wrapper(module, "ServerErrorMiddleware.debug_response", wrap_exception_handler)


def instrument_starlette_exceptions(module):
    wrap_function_wrapper(module, "ExceptionMiddleware.__call__", error_middleware_wrapper)

    wrap_function_wrapper(module, "ExceptionMiddleware.http_exception", wrap_exception_handler)

    wrap_function_wrapper(module, "ExceptionMiddleware.add_exception_handler", wrap_add_exception_handler)


def instrument_starlette_background_task(module):
    wrap_function_wrapper(module, "BackgroundTask.__call__", wrap_background_method)


def instrument_starlette_concurrency(module):
    wrap_function_wrapper(module, "run_in_threadpool", wrap_run_in_threadpool)
