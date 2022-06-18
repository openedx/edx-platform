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
import sys

from newrelic.api.application import application_instance
from newrelic.api.html_insertion import insert_html_snippet, verify_body_exists
from newrelic.api.transaction import current_transaction
from newrelic.api.web_transaction import WebTransaction
from newrelic.common.async_proxy import CoroutineProxy, LoopContext
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (
    FunctionWrapper,
    function_wrapper,
    wrap_object,
)
from newrelic.packages import asgiref_compatibility, six


def _bind_scope(scope, *args, **kwargs):
    return scope


def _bind_receive_send(scope, receive, send):
    return receive, send


async def coro_function_wrapper(coro_function, receive, send):
    return await coro_function(receive, send)


@function_wrapper
def double_to_single_callable(wrapped, instance, args, kwargs):
    scope = _bind_scope(*args, **kwargs)
    receive, send = _bind_receive_send(*args, **kwargs)
    coro_function = wrapped(scope)
    return coro_function_wrapper(coro_function, receive, send)


class ASGIBrowserMiddleware(object):
    def __init__(self, app, transaction=None, search_maximum=64 * 1024):
        self.app = app
        self.send = None
        self.messages = []
        self.initial_message = None
        self.body = b""
        self.more_body = True
        self.transaction = transaction
        self.search_maximum = search_maximum
        self.pass_through = not (transaction and transaction.enabled)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        self.send = send
        return await self.app(scope, receive, self.send_inject_browser_agent)

    async def send_buffered(self):
        self.pass_through = True
        await self.send(self.initial_message)
        await self.send(
            {
                "type": "http.response.body",
                "body": self.body,
                "more_body": self.more_body,
            }
        )
        # Clear any saved messages
        self.messages = None

    async def abort(self):
        self.pass_through = True
        for message in self.messages:
            await self.send(message)
        # Clear any saved messages
        self.messages = None

    def should_insert_html(self, headers):
        if self.transaction.autorum_disabled or self.transaction.rum_header_generated:
            return False

        content_encoding = None
        content_disposition = None
        content_type = None

        for header_name, header_value in headers:
            # assume header names are lower cased in accordance with ASGI spec
            if header_name == b"content-type":
                content_type = header_value
            elif header_name == b"content-encoding":
                content_encoding = header_value
            elif header_name == b"content-disposition":
                content_disposition = header_value

        if content_encoding is not None:
            # This will match any encoding, including if the
            # value 'identity' is used. Technically the value
            # 'identity' should only be used in the header
            # Accept-Encoding and not Content-Encoding. In
            # other words, a ASGI application should not be
            # returning identity. We could check and allow it
            # anyway and still do RUM insertion, but don't.

            return False

        if content_type is None:
            return False

        if content_disposition is not None and content_disposition.split(b";", 1)[0].strip().lower() == b"attachment":
            return False

        allowed_content_type = self.transaction.settings.browser_monitoring.content_type

        content_type = content_type.split(b";", 1)[0].decode("utf-8")

        if content_type not in allowed_content_type:
            return False

        return True

    async def send_inject_browser_agent(self, message):
        if self.pass_through:
            return await self.send(message)

        # Store messages in case of an abort
        self.messages.append(message)

        message_type = message["type"]
        if message_type == "http.response.start" and not self.initial_message:
            headers = list(message.get("headers", ()))
            if not self.should_insert_html(headers):
                await self.abort()
                return
            message["headers"] = headers
            self.initial_message = message
        elif message_type == "http.response.body" and self.initial_message:
            body = message.get("body", b"")
            self.more_body = message.get("more_body", False)

            # Add this message to the current body
            self.body += body

            # if there's a valid body string, attempt to insert the HTML
            if verify_body_exists(self.body):
                header = self.transaction.browser_timing_header()
                if not header:
                    # If there's no header, abort browser monitoring injection
                    await self.send_buffered()
                    return

                footer = self.transaction.browser_timing_footer()
                browser_agent_data = six.b(header) + six.b(footer)

                body = insert_html_snippet(self.body, lambda: browser_agent_data, self.search_maximum)

                # If we have inserted the browser agent
                if len(body) != len(self.body):
                    # check to see if we have to modify the content-length
                    # header
                    headers = self.initial_message["headers"]
                    for header_index, header_data in enumerate(headers):
                        header_name, header_value = header_data
                        if header_name.lower() == b"content-length":
                            break
                    else:
                        header_value, header_index = None, None

                    try:
                        content_length = int(header_value)
                    except ValueError:
                        # Invalid content length results in an abort
                        await self.send_buffered()
                        return

                    if content_length is not None:
                        delta = len(body) - len(self.body)
                        headers[header_index] = (
                            b"content-length",
                            str(content_length + delta).encode("utf-8"),
                        )

                    # Body is found and modified so we can now send the
                    # modified data and stop searching
                    self.body = body
                    await self.send_buffered()
                    return

            # 1. Body is found but not modified
            # 2. Body is not found

            # No more body
            if not self.more_body:
                await self.send_buffered()

            # We have hit our search limit
            elif len(self.body) >= self.search_maximum:
                await self.send_buffered()

        # Protocol error, unexpected message: abort
        else:
            await self.abort()


class ASGIWebTransaction(WebTransaction):
    def __init__(self, application, scope, receive, send):
        self.receive = receive
        self._send = send
        scheme = scope.get("scheme", "http")
        if "server" in scope and scope["server"] is not None:
            host, port = scope["server"] = tuple(scope["server"])
        else:
            host, port = None, None
        request_method = scope["method"]
        request_path = scope["path"]
        query_string = scope["query_string"]
        headers = scope["headers"] = tuple(scope["headers"])
        super(ASGIWebTransaction, self).__init__(
            application=application,
            name=None,
            scheme=scheme,
            host=host,
            port=port,
            request_method=request_method,
            request_path=request_path,
            query_string=query_string,
            headers=headers,
        )

        if self._settings:
            self.capture_params = self._settings.capture_params

    async def send(self, event):
        if event["type"] == "http.response.body" and not event.get("more_body", False):
            try:
                return await self._send(event)
            finally:
                self.__exit__(*sys.exc_info())
        elif event["type"] == "http.response.start":
            self.process_response(event["status"], event.get("headers", ()))
        return await self._send(event)


def ASGIApplicationWrapper(wrapped, application=None, name=None, group=None, framework=None):
    def nr_asgi_wrapper(wrapped, instance, args, kwargs):
        double_callable = asgiref_compatibility.is_double_callable(wrapped)
        if double_callable:
            is_v2_signature = (len(args) + len(kwargs)) == 1
            if not is_v2_signature:
                return wrapped(*args, **kwargs)

        scope = _bind_scope(*args, **kwargs)

        if scope["type"] != "http":
            return wrapped(*args, **kwargs)

        async def nr_async_asgi(receive, send):
            # Check to see if any transaction is present, even an inactive
            # one which has been marked to be ignored or which has been
            # stopped already.

            transaction = current_transaction(active_only=False)

            if transaction:
                # If there is any active transaction we will return without
                # applying a new ASGI application wrapper context. In the
                # case of a transaction which is being ignored or which has
                # been stopped, we do that without doing anything further.

                if transaction.ignore_transaction or transaction.stopped:
                    return await wrapped(scope, receive, send)

                # For any other transaction, we record the details of any
                # framework against the transaction for later reporting as
                # supportability metrics.

                if framework:
                    transaction.add_framework_info(name=framework[0], version=framework[1])

                # Also override the web transaction name to be the name of
                # the wrapped callable if not explicitly named, and we want
                # the default name to be that of the ASGI component for the
                # framework. This will override the use of a raw URL which
                # can result in metric grouping issues where a framework is
                # not instrumented or is leaking URLs.

                settings = transaction._settings

                if name is None and settings:
                    if framework is not None:
                        naming_scheme = settings.transaction_name.naming_scheme
                        if naming_scheme in (None, "framework"):
                            transaction.set_transaction_name(callable_name(wrapped), priority=1)

                elif name:
                    transaction.set_transaction_name(name, group, priority=1)

                return await wrapped(scope, receive, send)

            with ASGIWebTransaction(
                application=application_instance(application),
                scope=scope,
                receive=receive,
                send=send,
            ) as transaction:

                # Record details of framework against the transaction for later
                # reporting as supportability metrics.
                if framework:
                    transaction.add_framework_info(name=framework[0], version=framework[1])

                # Override the initial web transaction name to be the supplied
                # name, or the name of the wrapped callable if wanting to use
                # the callable as the default. This will override the use of a
                # raw URL which can result in metric grouping issues where a
                # framework is not instrumented or is leaking URLs.
                #
                # Note that at present if default for naming scheme is still
                # None and we aren't specifically wrapping a designated
                # framework, then we still allow old URL based naming to
                # override. When we switch to always forcing a name we need to
                # check for naming scheme being None here.

                settings = transaction._settings

                if name is None and settings:
                    naming_scheme = settings.transaction_name.naming_scheme

                    if framework is not None:
                        if naming_scheme in (None, "framework"):
                            transaction.set_transaction_name(callable_name(wrapped), priority=1)

                    elif naming_scheme in ("component", "framework"):
                        transaction.set_transaction_name(callable_name(wrapped), priority=1)

                elif name:
                    transaction.set_transaction_name(name, group, priority=1)

                if settings and settings.browser_monitoring.enabled and not transaction.autorum_disabled:
                    app = ASGIBrowserMiddleware(wrapped, transaction)
                else:
                    app = wrapped
                coro = app(scope, transaction.receive, transaction.send)
                coro = CoroutineProxy(coro, LoopContext())
                return await coro

        if double_callable:
            wrapped = double_to_single_callable(wrapped)
            return nr_async_asgi
        else:
            return nr_async_asgi(*_bind_receive_send(*args, **kwargs))

    return FunctionWrapper(wrapped, nr_asgi_wrapper)


def asgi_application(application=None, name=None, group=None, framework=None):
    return functools.partial(
        ASGIApplicationWrapper,
        application=application,
        name=name,
        group=group,
        framework=framework,
    )


def wrap_asgi_application(module, object_path, application=None, name=None, group=None, framework=None):
    wrap_object(
        module,
        object_path,
        ASGIApplicationWrapper,
        (application, name, group, framework),
    )
