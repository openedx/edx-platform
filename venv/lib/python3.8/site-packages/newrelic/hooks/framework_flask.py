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

"""Instrumentation module for Flask framework.

"""

from newrelic.api.function_trace import (
    FunctionTrace,
    FunctionTraceWrapper,
    wrap_function_trace,
)
from newrelic.api.time_trace import notice_error
from newrelic.api.transaction import current_transaction
from newrelic.api.wsgi_application import wrap_wsgi_application
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import function_wrapper, wrap_function_wrapper


def framework_details():
    import flask

    return ("Flask", getattr(flask, "__version__", None))


def status_code(exc, value, tb):
    from werkzeug.exceptions import HTTPException

    # Werkzeug HTTPException can be raised internally by Flask or in
    # user code if they mix Flask with Werkzeug. Filter based on the
    # HTTP status code.

    if isinstance(value, HTTPException):
        return value.code


@function_wrapper
def _nr_wrapper_handler_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = getattr(wrapped, "_nr_view_func_name", callable_name(wrapped))

    # Set priority=2 so this will take precedence over any error
    # handler which will be at priority=1.

    transaction.set_transaction_name(name, priority=2)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)


def _nr_wrapper_Flask_add_url_rule_input_(wrapped, instance, args, kwargs):
    def _bind_params(rule, endpoint=None, view_func=None, **options):
        return rule, endpoint, view_func, options

    rule, endpoint, view_func, options = _bind_params(*args, **kwargs)

    if view_func is not None:
        view_func = _nr_wrapper_handler_(view_func)

    return wrapped(rule, endpoint, view_func, **options)


def _nr_wrapper_Flask_views_View_as_view_(wrapped, instance, args, kwargs):
    view = wrapped(*args, **kwargs)
    view._nr_view_func_name = "%s:%s" % (view.__module__, view.__name__)
    return view


@function_wrapper
def _nr_wrapper_endpoint_(wrapped, instance, args, kwargs):
    def _bind_params(f, *args, **kwargs):
        return f

    f = _bind_params(*args, **kwargs)

    return wrapped(_nr_wrapper_handler_(f))


def _nr_wrapper_Flask_endpoint_(wrapped, instance, args, kwargs):
    return _nr_wrapper_endpoint_(wrapped(*args, **kwargs))


def _nr_wrapper_Flask_handle_http_exception_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    # Because we use priority=1, this name will only be used in cases
    # where an error handler was called without an actual request
    # handler having already being called.

    transaction.set_transaction_name(name, priority=1)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)


def _nr_wrapper_Flask_handle_exception_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    # The Flask.handle_exception() method is always called in the
    # context of the except clause of the try block. We can therefore
    # rely on grabbing current exception details so we have access to
    # the addition stack trace information.
    notice_error(status_code=status_code)

    name = callable_name(wrapped)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)


@function_wrapper
def _nr_wrapper_error_handler_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    # Because we use priority=1, this name will only be used in cases
    # where an error handler was called without an actual request
    # handler having already being called.

    transaction.set_transaction_name(name, priority=1)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)


def _nr_wrapper_Flask__register_error_handler_(wrapped, instance, args, kwargs):
    def _bind_params(key, code_or_exception, f):
        return key, code_or_exception, f

    key, code_or_exception, f = _bind_params(*args, **kwargs)

    f = _nr_wrapper_error_handler_(f)

    return wrapped(key, code_or_exception, f)


def _nr_wrapper_Flask_register_error_handler_(wrapped, instance, args, kwargs):
    def _bind_params(code_or_exception, f):
        return code_or_exception, f

    code_or_exception, f = _bind_params(*args, **kwargs)

    f = _nr_wrapper_error_handler_(f)

    return wrapped(code_or_exception, f)


def _nr_wrapper_Flask_try_trigger_before_first_request_functions_(wrapped, instance, args, kwargs):

    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    if not instance.before_first_request_funcs:
        return wrapped(*args, **kwargs)

    if instance._got_first_request:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    transaction.set_transaction_name(name)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)


def _nr_wrapper_Flask_before_first_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


@function_wrapper
def _nr_wrapper_Flask_before_request_wrapped_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    transaction.set_transaction_name(name)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)


def _nr_wrapper_Flask_before_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = _nr_wrapper_Flask_before_request_wrapped_(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Flask_after_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Flask_teardown_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Flask_teardown_appcontext_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


def instrument_flask_views(module):
    wrap_function_wrapper(module, "View.as_view", _nr_wrapper_Flask_views_View_as_view_)


def instrument_flask_app(module):
    wrap_wsgi_application(module, "Flask.wsgi_app", framework=framework_details)

    wrap_function_wrapper(module, "Flask.add_url_rule", _nr_wrapper_Flask_add_url_rule_input_)

    if hasattr(module.Flask, "endpoint"):
        wrap_function_wrapper(module, "Flask.endpoint", _nr_wrapper_Flask_endpoint_)

    wrap_function_wrapper(module, "Flask.handle_http_exception", _nr_wrapper_Flask_handle_http_exception_)

    # Use the same wrapper for initial user exception processing and
    # fallback for unhandled exceptions.

    if hasattr(module.Flask, "handle_user_exception"):
        wrap_function_wrapper(module, "Flask.handle_user_exception", _nr_wrapper_Flask_handle_exception_)

    wrap_function_wrapper(module, "Flask.handle_exception", _nr_wrapper_Flask_handle_exception_)

    # The _register_error_handler() method was only introduced in
    # Flask version 0.7.0.
    if hasattr(module.Flask, "_register_error_handler"):
        wrap_function_wrapper(
            module,
            "Flask._register_error_handler",
            _nr_wrapper_Flask__register_error_handler_,
        )

    # The method changed name to register_error_handler() in
    # Flask version 2.0.0.
    elif hasattr(module.Flask, "register_error_handler"):
        wrap_function_wrapper(
            module,
            "Flask.register_error_handler",
            _nr_wrapper_Flask_register_error_handler_,
        )

    # Different before/after methods were added in different versions.
    # Check for the presence of everything before patching.

    if hasattr(module.Flask, "try_trigger_before_first_request_functions"):
        wrap_function_wrapper(
            module,
            "Flask.try_trigger_before_first_request_functions",
            _nr_wrapper_Flask_try_trigger_before_first_request_functions_,
        )
        wrap_function_wrapper(
            module,
            "Flask.before_first_request",
            _nr_wrapper_Flask_before_first_request_,
        )

    if hasattr(module.Flask, "preprocess_request"):
        wrap_function_trace(module, "Flask.preprocess_request")
        wrap_function_wrapper(module, "Flask.before_request", _nr_wrapper_Flask_before_request_)

    if hasattr(module.Flask, "process_response"):
        wrap_function_trace(module, "Flask.process_response")
        wrap_function_wrapper(module, "Flask.after_request", _nr_wrapper_Flask_after_request_)

    if hasattr(module.Flask, "do_teardown_request"):
        wrap_function_trace(module, "Flask.do_teardown_request")
        wrap_function_wrapper(module, "Flask.teardown_request", _nr_wrapper_Flask_teardown_request_)

    if hasattr(module.Flask, "do_teardown_appcontext"):
        wrap_function_trace(module, "Flask.do_teardown_appcontext")
        wrap_function_wrapper(module, "Flask.teardown_appcontext", _nr_wrapper_Flask_teardown_appcontext_)


def instrument_flask_templating(module):
    wrap_function_trace(module, "render_template")
    wrap_function_trace(module, "render_template_string")


def _nr_wrapper_Blueprint_endpoint_(wrapped, instance, args, kwargs):
    return _nr_wrapper_endpoint_(wrapped(*args, **kwargs))


@function_wrapper
def _nr_wrapper_Blueprint_before_request_wrapped_(wrapped, instance, args, kwargs):

    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    transaction.set_transaction_name(name)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)


def _nr_wrapper_Blueprint_before_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = _nr_wrapper_Blueprint_before_request_wrapped_(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Blueprint_before_app_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = _nr_wrapper_Blueprint_before_request_wrapped_(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Blueprint_before_app_first_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Blueprint_after_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Blueprint_after_app_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Blueprint_teardown_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


def _nr_wrapper_Blueprint_teardown_app_request_(wrapped, instance, args, kwargs):
    def _params(f, *args, **kwargs):
        return f, args, kwargs

    f, _args, _kwargs = _params(*args, **kwargs)
    f = FunctionTraceWrapper(f)

    return wrapped(f, *_args, **_kwargs)


def instrument_flask_blueprints(module):
    wrap_function_wrapper(module, "Blueprint.endpoint", _nr_wrapper_Blueprint_endpoint_)

    if hasattr(module.Blueprint, "before_request"):
        wrap_function_wrapper(module, "Blueprint.before_request", _nr_wrapper_Blueprint_before_request_)
    if hasattr(module.Blueprint, "before_app_request"):
        wrap_function_wrapper(
            module,
            "Blueprint.before_app_request",
            _nr_wrapper_Blueprint_before_app_request_,
        )
    if hasattr(module.Blueprint, "before_app_first_request"):
        wrap_function_wrapper(
            module,
            "Blueprint.before_app_first_request",
            _nr_wrapper_Blueprint_before_app_first_request_,
        )

    if hasattr(module.Blueprint, "after_request"):
        wrap_function_wrapper(module, "Blueprint.after_request", _nr_wrapper_Blueprint_after_request_)
    if hasattr(module.Blueprint, "after_app_request"):
        wrap_function_wrapper(
            module,
            "Blueprint.after_app_request",
            _nr_wrapper_Blueprint_after_app_request_,
        )

    if hasattr(module.Blueprint, "teardown_request"):
        wrap_function_wrapper(
            module,
            "Blueprint.teardown_request",
            _nr_wrapper_Blueprint_teardown_request_,
        )
    if hasattr(module.Blueprint, "teardown_app_request"):
        wrap_function_wrapper(
            module,
            "Blueprint.teardown_app_request",
            _nr_wrapper_Blueprint_teardown_app_request_,
        )
