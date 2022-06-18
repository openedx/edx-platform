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
import textwrap
import inspect
import sys
import time
from newrelic.api.function_trace import function_trace
from newrelic.api.transaction import current_transaction
from newrelic.api.external_trace import ExternalTrace
from newrelic.api.time_trace import notice_error
from newrelic.api.web_transaction import WebTransaction
from newrelic.api.application import application_instance
from newrelic.core.trace_cache import trace_cache
from newrelic.common.object_wrapper import (
        function_wrapper, wrap_function_wrapper)
from newrelic.common.async_proxy import async_proxy
from newrelic.common.object_names import callable_name


_VERSION = None
_instrumented = set()


def _store_version_info():
    import tornado
    global _VERSION

    try:
        _VERSION = '.'.join(map(str, tornado.version_info))
    except:
        pass

    return tornado.version_info


def convert_yielded(*args, **kwargs):
    global convert_yielded
    from tornado.gen import convert_yielded as _convert_yielded
    convert_yielded = _convert_yielded
    return _convert_yielded(*args, **kwargs)


def _wrap_if_not_wrapped(obj, attr, wrapper):
    wrapped = getattr(obj, attr, None)

    if not callable(wrapped):
        return

    if not (hasattr(wrapped, '__wrapped__') and
            wrapped.__wrapped__ in _instrumented):
        setattr(obj, attr, wrapper(wrapped))
        _instrumented.add(wrapped)


def _bind_start_request(server_conn, request_conn, *args, **kwargs):
    return request_conn


def _bind_headers_received(start_line, headers, *args, **kwargs):
    return start_line, headers


def wrap_headers_received(request_conn):

    @function_wrapper
    def _wrap_headers_received(wrapped, instance, args, kwargs):
        start_line, headers = _bind_headers_received(*args, **kwargs)
        port = None

        try:
            # We only want to record port for ipv4 and ipv6 socket families.
            # Unix socket will just return a string instead of a tuple, so
            # skip this.
            sockname = request_conn.stream.socket.getsockname()
            if isinstance(sockname, tuple):
                port = sockname[1]
        except:
            pass

        path, sep, query = start_line.path.partition('?')

        transaction = WebTransaction(
            application=application_instance(),
            name=callable_name(instance),
            port=port,
            request_method=start_line.method,
            request_path=path,
            query_string=query,
            headers=headers,
        )
        transaction.__enter__()

        if not transaction.enabled:
            return wrapped(*args, **kwargs)

        transaction.add_framework_info('Tornado', _VERSION)

        # Store the transaction on the HTTPMessageDelegate object since the
        # transaction lives for the lifetime of that object.
        request_conn._nr_transaction = transaction

        # Remove the headers_received circular reference
        vars(instance).pop('headers_received')

        return wrapped(*args, **kwargs)

    return _wrap_headers_received


def _bind_response_headers(start_line, headers, *args, **kwargs):
    return start_line.code, headers


@function_wrapper
def wrap_write_headers(wrapped, instance, args, kwargs):
    transaction = getattr(instance, '_nr_transaction', None)

    if transaction:
        http_status, headers = _bind_response_headers(*args, **kwargs)
        cat_headers = transaction.process_response(http_status, headers)

        for name, value in cat_headers:
            headers.add(name, value)

    return wrapped(*args, **kwargs)


@function_wrapper
def wrap_finish(wrapped, instance, args, kwargs):
    try:
        return wrapped(*args, **kwargs)
    finally:
        transaction = getattr(instance, '_nr_transaction', None)
        if transaction:
            start_time = getattr(transaction, '_async_start_time', None)
            if start_time:
                trace_cache().record_event_loop_wait(start_time, time.time())
                transaction._async_start_time = None
            notice_error(
                    sys.exc_info(),
                    status_code=status_code)
            transaction.__exit__(None, None, None)
            instance._nr_transaction = None


def wrap_start_request(wrapped, instance, args, kwargs):
    request_conn = _bind_start_request(*args, **kwargs)
    message_delegate = wrapped(*args, **kwargs)

    # Wrap headers_received (request method / path is known)
    wrapper = wrap_headers_received(request_conn)
    message_delegate.headers_received = wrapper(
            message_delegate.headers_received)

    # Wrap write_headers to get response
    _wrap_if_not_wrapped(
            type(request_conn), 'write_headers', wrap_write_headers)

    # Wrap finish (response has been written)
    _wrap_if_not_wrapped(
            type(request_conn), 'finish', wrap_finish)

    return message_delegate


def instrument_tornado_httpserver(module):
    version_info = _store_version_info()

    # Do not instrument Tornado versions < 6.0
    if version_info[0] < 6:
        return

    wrap_function_wrapper(
            module, 'HTTPServer.start_request', wrap_start_request)


def status_code(exc, value, tb):
    from tornado.web import HTTPError

    if exc is HTTPError:
        return value.status_code


def _nr_wrapper__NormalizedHeaderCache___missing__(
        wrapped, instance, args, kwargs):

    def _bind_params(key, *args, **kwargs):
        return key

    key = _bind_params(*args, **kwargs)

    normalized = wrapped(*args, **kwargs)

    if key.startswith('X-NewRelic'):
        instance[key] = key
        return key

    return normalized


def _nr_wrapper_normalize_header(wrapped, instance, args, kwargs):
    def _bind_params(name, *args, **kwargs):
        return name

    name = _bind_params(*args, **kwargs)
    if name.startswith('X-NewRelic'):
        return name

    return wrapped(*args, **kwargs)


def instrument_tornado_httputil(module):
    version_info = _store_version_info()

    # Do not instrument Tornado versions < 6.0
    if version_info[0] < 6:
        return

    if hasattr(module, '_NormalizedHeaderCache'):
        wrap_function_wrapper(module, '_NormalizedHeaderCache.__missing__',
                _nr_wrapper__NormalizedHeaderCache___missing__)
    elif hasattr(module, '_normalize_header'):
        wrap_function_wrapper(module, '_normalize_header',
                _nr_wrapper_normalize_header)


def _prepare_request(request, raise_error=True, **kwargs):
    from tornado.httpclient import HTTPRequest

    # request is either a string or a HTTPRequest object
    if not isinstance(request, HTTPRequest):
        request = HTTPRequest(request, **kwargs)

    return request, raise_error


def create_client_wrapper(wrapped, trace):
    values = {'wrapper': None, 'wrapped': wrapped,
            'trace': trace, 'functools': functools}
    wrapper = textwrap.dedent("""
    @functools.wraps(wrapped)
    async def wrapper(req, raise_error):
        with trace:
            response = None
            try:
                response = await wrapped(req, raise_error=raise_error)
            except Exception as e:
                response = getattr(e, 'response', None)
                raise
            finally:
                if response:
                    trace.process_response_headers(response.headers.get_all())
            return response
    """)
    exec(wrapper, values)
    return values['wrapper']


def wrap_httpclient_fetch(wrapped, instance, args, kwargs):
    try:
        req, raise_error = _prepare_request(*args, **kwargs)
    except:
        return wrapped(*args, **kwargs)

    trace = ExternalTrace(
            'tornado', req.url, req.method.upper())

    outgoing_headers = trace.generate_request_headers(current_transaction())
    for header_name, header_value in outgoing_headers:
        # User headers should override our CAT headers
        if header_name in req.headers:
            continue
        req.headers[header_name] = header_value

    try:
        fetch = create_client_wrapper(wrapped, trace)
    except:
        return wrapped(*args, **kwargs)

    return convert_yielded(fetch(req, raise_error))


def instrument_tornado_httpclient(module):
    version_info = _store_version_info()

    # Do not instrument Tornado versions < 6.0
    if version_info[0] < 6:
        return

    wrap_function_wrapper(module,
            'AsyncHTTPClient.fetch', wrap_httpclient_fetch)


def _nr_rulerouter_process_rule(wrapped, instance, args, kwargs):
    def _bind_params(rule, *args, **kwargs):
        return rule

    rule = _bind_params(*args, **kwargs)

    _wrap_handlers(rule)

    return wrapped(*args, **kwargs)


@function_wrapper
def _nr_method(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    if getattr(transaction, '_method_seen', None):
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)
    transaction.set_transaction_name(name, priority=2)
    transaction._method_seen = True
    if getattr(wrapped, '__tornado_coroutine__', False):
        return wrapped(*args, **kwargs)
    return function_trace(name=name)(wrapped)(*args, **kwargs)


def _wrap_handlers(rule):
    if isinstance(rule, (tuple, list)):
        handler = rule[1]
    elif hasattr(rule, 'target'):
        handler = rule.target
    elif hasattr(rule, 'handler_class'):
        handler = rule.handler_class
    else:
        return

    from tornado.web import RequestHandler
    from tornado.websocket import WebSocketHandler

    if isinstance(handler, (tuple, list)):
        # Tornado supports nested rules. For example
        #
        # application = web.Application([
        #     (HostMatches("example.com"), [
        #         (r"/", MainPageHandler),
        #         (r"/feed", FeedHandler),
        #     ]),
        # ])
        for subrule in handler:
            _wrap_handlers(subrule)
        return

    elif (not inspect.isclass(handler) or
            issubclass(handler, WebSocketHandler) or
            not issubclass(handler, RequestHandler)):
        # This handler does not inherit from RequestHandler so we ignore it.
        # Tornado supports non class based views and this is probably one of
        # those. It has also been observed that tornado's internals will pass
        # class instances as well.
        return

    if not hasattr(handler, 'SUPPORTED_METHODS'):
        return

    # Wrap all supported view methods with our FunctionTrace
    # instrumentation
    for request_method in handler.SUPPORTED_METHODS:
        _wrap_if_not_wrapped(handler, request_method.lower(), _nr_method)


def _nr_wrapper_web_requesthandler_init(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(instance)
    transaction.set_transaction_name(name, priority=1)
    return wrapped(*args, **kwargs)


def instrument_tornado_routing(module):
    version_info = _store_version_info()

    # Do not instrument Tornado versions < 6.0
    if version_info[0] < 6:
        return

    wrap_function_wrapper(module, 'RuleRouter.process_rule',
            _nr_rulerouter_process_rule)


def instrument_tornado_web(module):
    version_info = _store_version_info()

    # Do not instrument Tornado versions < 6.0
    if version_info[0] < 6:
        return

    wrap_function_wrapper(module, 'RequestHandler.__init__',
            _nr_wrapper_web_requesthandler_init)
    wrap_function_wrapper(module, 'RequestHandler._execute',
            track_loop_time)


class TornadoContext(object):
    def __init__(self):
        self.transaction = None

    def __enter__(self):
        transaction = self.transaction
        if not transaction:
            transaction = self.transaction = current_transaction()

        if transaction:
            transaction._async_start_time = time.time()

    def __exit__(self, exc, value, tb):
        if self.transaction:
            start_time = self.transaction._async_start_time
            if start_time:
                trace_cache().record_event_loop_wait(start_time, time.time())


def track_loop_time(wrapped, instance, args, kwargs):
    proxy = async_proxy(wrapped)
    if proxy:
        return proxy(wrapped(*args, **kwargs), TornadoContext())

    return wrapped(*args, **kwargs)
