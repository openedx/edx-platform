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
import logging
import sys
import time

from newrelic.api.application import application_instance
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.html_insertion import insert_html_snippet, verify_body_exists
from newrelic.api.time_trace import notice_error
from newrelic.api.transaction import current_transaction
from newrelic.api.web_transaction import WSGIWebTransaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.packages import six

_logger = logging.getLogger(__name__)


class _WSGIApplicationIterable(object):
    def __init__(self, transaction, generator):
        self.transaction = transaction
        self.generator = generator
        self.response_trace = None
        self.closed = False

    def __iter__(self):
        self.start_trace()

        try:
            for item in self.generator:
                try:
                    self.transaction._calls_yield += 1
                    self.transaction._bytes_sent += len(item)
                except Exception:
                    pass

                yield item

        except GeneratorExit:
            raise

        except:  # Catch all
            notice_error()
            raise

        finally:
            self.close()

    def start_trace(self):
        if not self.transaction._sent_start:
            self.transaction._sent_start = time.time()

        if not self.response_trace:
            self.response_trace = FunctionTrace(name="Response", group="Python/WSGI")
            self.response_trace.__enter__()

    def close(self):
        if self.closed:
            return

        if self.response_trace:
            self.response_trace.__exit__(None, None, None)
            self.response_trace = None

        try:
            with FunctionTrace(name="Finalize", group="Python/WSGI"):

                if isinstance(self.generator, _WSGIApplicationMiddleware):
                    self.generator.close()

                elif hasattr(self.generator, "close"):
                    name = callable_name(self.generator.close)
                    with FunctionTrace(name):
                        self.generator.close()

        except:  # Catch all
            self.transaction.__exit__(*sys.exc_info())
            raise

        else:
            self.transaction.__exit__(None, None, None)
            self.transaction._sent_end = time.time()

        finally:
            self.closed = True


class _WSGIInputWrapper(object):
    def __init__(self, transaction, input):
        self.__transaction = transaction
        self.__input = input

    def __getattr__(self, name):
        return getattr(self.__input, name)

    def close(self):
        if hasattr(self.__input, "close"):
            self.__input.close()

    def read(self, *args, **kwargs):
        if not self.__transaction._read_start:
            self.__transaction._read_start = time.time()
        try:
            data = self.__input.read(*args, **kwargs)
            try:
                self.__transaction._calls_read += 1
                self.__transaction._bytes_read += len(data)
            except Exception:
                pass
        finally:
            self.__transaction._read_end = time.time()
        return data

    def readline(self, *args, **kwargs):
        if not self.__transaction._read_start:
            self.__transaction._read_start = time.time()
        try:
            line = self.__input.readline(*args, **kwargs)
            try:
                self.__transaction._calls_readline += 1
                self.__transaction._bytes_read += len(line)
            except Exception:
                pass
        finally:
            self.__transaction._read_end = time.time()
        return line

    def readlines(self, *args, **kwargs):
        if not self.__transaction._read_start:
            self.__transaction._read_start = time.time()
        try:
            lines = self.__input.readlines(*args, **kwargs)
            try:
                self.__transaction._calls_readlines += 1
                self.__transaction._bytes_read += sum(map(len, lines))
            except Exception:
                pass
        finally:
            self.__transaction._read_end = time.time()
        return lines


class _WSGIApplicationMiddleware(object):

    # This is a WSGI middleware for automatically inserting RUM into
    # HTML responses. It only works for where a WSGI application is
    # returning response content via a iterable/generator. It does not
    # work if the WSGI application write() callable is being used. It
    # will buffer response content up to the start of <body>. This is
    # technically in violation of the WSGI specification if one is
    # strict, but will still work with all known WSGI servers. Because
    # it does buffer, then technically it may cause a problem with
    # streamed responses. For that to occur then it would have to be a
    # HTML response that doesn't actually use <body> and so technically
    # is not a valid HTML response. It is assumed though that in
    # streaming a response, the <head> itself isn't streamed out only
    # gradually.

    search_maximum = 64 * 1024

    def __init__(self, application, environ, start_response, transaction):
        self.application = application

        self.pass_through = True

        self.request_environ = environ
        self.outer_start_response = start_response
        self.outer_write = None

        self.transaction = transaction

        self.response_status = None
        self.response_headers = []
        self.response_args = ()

        self.content_length = None

        self.response_length = 0
        self.response_data = []

        settings = transaction.settings

        self.debug = settings and settings.debug.log_autorum_middleware

        # Grab the iterable returned by the wrapped WSGI
        # application.
        self.iterable = self.application(self.request_environ, self.start_response)

    def process_data(self, data):
        # If this is the first data block, then immediately try
        # for an insertion using full set of criteria. If this
        # works then we are done, else we move to next phase of
        # buffering up content until we find the body element.

        def html_to_be_inserted():
            header = self.transaction.browser_timing_header()

            if not header:
                return b""

            footer = self.transaction.browser_timing_footer()

            return six.b(header) + six.b(footer)

        if not self.response_data:
            modified = insert_html_snippet(data, html_to_be_inserted)

            if modified is not None:
                if self.debug:
                    _logger.debug(
                        "RUM insertion from WSGI middleware "
                        "triggered on first yielded string from "
                        "response. Bytes added was %r.",
                        len(modified) - len(data),
                    )

                if self.content_length is not None:
                    length = len(modified) - len(data)
                    self.content_length += length

                return [modified]

        # Buffer up the data. If we haven't found the start of
        # the body element, that is all we do. If we have reached
        # the limit of buffering allowed, then give up and return
        # the buffered data.

        if not self.response_data or not verify_body_exists(data):
            self.response_length += len(data)
            self.response_data.append(data)

            if self.response_length >= self.search_maximum:
                buffered_data = self.response_data
                self.response_data = []
                return buffered_data

            return

        # Now join back together any buffered data into a single
        # string. This makes it easier to process, but there is a
        # risk that we could temporarily double memory use for
        # the response content if had small data blocks followed
        # by very large data block. Expect that the risk of this
        # occurring is very small.

        if self.response_data:
            self.response_data.append(data)
            data = b"".join(self.response_data)
            self.response_data = []

        # Perform the insertion of the HTML. This should always
        # succeed as we would only have got here if we had found
        # the body element, which is the fallback point for
        # insertion.

        modified = insert_html_snippet(data, html_to_be_inserted)

        if modified is not None:
            if self.debug:
                _logger.debug(
                    "RUM insertion from WSGI middleware "
                    "triggered on subsequent string yielded from "
                    "response. Bytes added was %r.",
                    len(modified) - len(data),
                )

            if self.content_length is not None:
                length = len(modified) - len(data)
                self.content_length += length

            return [modified]

        # Something went very wrong as we should never get here.

        return [data]

    def flush_headers(self):
        # Add back in any response content length header. It will
        # have been updated with the adjusted length by now if
        # additional data was inserted into the response.

        if self.content_length is not None:
            header = ("Content-Length", str(self.content_length))
            self.response_headers.append(header)

        self.outer_write = self.outer_start_response(self.response_status, self.response_headers, *self.response_args)

    def inner_write(self, data):
        # If the write() callable is used, we do not attempt to
        # do any insertion at all here after.

        self.pass_through = True

        # Flush the response headers if this hasn't yet been done.

        if self.outer_write is None:
            self.flush_headers()

        # Now write out any buffered response data in case the
        # WSGI application was doing something evil where it
        # mixed use of yield and write. Technically if write()
        # is used, it is supposed to be before any attempt to
        # yield a string. When done switch to pass through mode.

        if self.response_data:
            for buffered_data in self.response_data:
                self.outer_write(buffered_data)
            self.response_data = []

        return self.outer_write(data)

    def start_response(self, status, response_headers, *args):
        # The start_response() function can be called more than
        # once. In that case, the values derived from the most
        # recent call are used. We therefore need to reset any
        # calculated values.

        self.pass_through = True

        self.response_status = status
        self.response_headers = response_headers
        self.response_args = args

        self.content_length = None

        # We need to check again if auto RUM has been disabled.
        # This is because it can be disabled using an API call.
        # Also check whether RUM insertion has already occurred.

        if self.transaction.autorum_disabled or self.transaction.rum_header_generated:

            self.flush_headers()
            self.pass_through = True

            return self.inner_write

        # Extract values for response headers we need to work. Do
        # not copy across the content length header at this time
        # as we will need to adjust the length later if we are
        # able to inject our Javascript.

        pass_through = False

        headers = []

        content_type = None
        content_length = None
        content_encoding = None
        content_disposition = None

        for (name, value) in response_headers:
            _name = name.lower()

            if _name == "content-length":
                try:
                    content_length = int(value)
                    continue

                except ValueError:
                    pass_through = True

            elif _name == "content-type":
                content_type = value

            elif _name == "content-encoding":
                content_encoding = value

            elif _name == "content-disposition":
                content_disposition = value

            headers.append((name, value))

        # We can only inject our Javascript if the content type
        # is an allowed value, no content encoding has been set
        # and an attachment isn't being used.

        def should_insert_html():
            if pass_through:
                return False

            if content_encoding is not None:
                # This will match any encoding, including if the
                # value 'identity' is used. Technically the value
                # 'identity' should only be used in the header
                # Accept-Encoding and not Content-Encoding. In
                # other words, a WSGI application should not be
                # returning identity. We could check and allow it
                # anyway and still do RUM insertion, but don't.

                return False

            if content_disposition is not None and content_disposition.split(";")[0].strip().lower() == "attachment":
                return False

            if content_type is None:
                return False

            settings = self.transaction.settings
            allowed_content_type = settings.browser_monitoring.content_type

            if content_type.split(";")[0] not in allowed_content_type:
                return False

            return True

        if should_insert_html():
            self.pass_through = False

            self.content_length = content_length
            self.response_headers = headers

        # If in pass through mode at this point, we need to flush
        # out the headers. We technically might do this again
        # later if start_response() was called more than once.

        if self.pass_through:
            self.flush_headers()

        return self.inner_write

    def close(self):
        # Call close() on the iterable as required by the
        # WSGI specification.

        if hasattr(self.iterable, "close"):
            name = callable_name(self.iterable.close)
            with FunctionTrace(name):
                self.iterable.close()

    def __iter__(self):
        # Process the response content from the iterable.

        for data in self.iterable:
            # If we are in pass through mode, simply pass it
            # through. If we are in pass through mode then
            # the headers should already have been flushed.

            if self.pass_through:
                yield data

                continue

            # If the headers haven't been flushed we need to
            # check for the potential insertion point and
            # buffer up data as necessary if we can't find it.

            if self.outer_write is None:
                # Ignore any empty strings.

                if not data:
                    continue

                # Check for the insertion point. Will return
                # None if data was buffered.

                buffered_data = self.process_data(data)

                if buffered_data is None:
                    continue

                # The data was returned, with it being
                # potentially modified. It would not have
                # been modified if we had reached maximum to
                # be buffer. Flush out the headers, switch to
                # pass through mode and yield the data.

                self.flush_headers()
                self.pass_through = True

                for data in buffered_data:
                    yield data

            else:
                # Depending on how the WSGI specification is
                # interpreted, this shouldn't occur. That is,
                # nothing should be yielded prior to the
                # start_response() function being called. The
                # CGI/WSGI example in the WSGI specification
                # does allow that though as do various WSGI
                # servers that followed that example.

                yield data

        # Ensure that headers have been written if the
        # response was actually empty.

        if self.outer_write is None:
            self.flush_headers()
            self.pass_through = True

        # Ensure that any remaining buffered data is also
        # written. Technically this should never be able
        # to occur at this point, but do it just in case.

        if self.response_data:
            for data in self.response_data:
                yield data


def WSGIApplicationWrapper(wrapped, application=None, name=None, group=None, framework=None):

    # Python 2 does not allow rebinding nonlocal variables, so to fix this
    # framework must be stored in list so it can be edited by closure.
    _framework = [framework]

    def get_framework():
        """Used to delay imports by passing framework as a callable."""
        framework = _framework[0]
        if isinstance(framework, tuple) or framework is None:
            return framework

        if callable(framework):
            framework = framework()
            _framework[0] = framework

        if framework is not None and not isinstance(framework, tuple):
            framework = (framework, None)
            _framework[0] = framework

        return framework

    def _nr_wsgi_application_wrapper_(wrapped, instance, args, kwargs):
        # Check to see if any transaction is present, even an inactive
        # one which has been marked to be ignored or which has been
        # stopped already.

        transaction = current_transaction(active_only=False)
        framework = get_framework()

        if transaction:
            # If there is any active transaction we will return without
            # applying a new WSGI application wrapper context. In the
            # case of a transaction which is being ignored or which has
            # been stopped, we do that without doing anything further.

            if transaction.ignore_transaction or transaction.stopped:
                return wrapped(*args, **kwargs)

            # For any other transaction, we record the details of any
            # framework against the transaction for later reporting as
            # supportability metrics.

            if framework:
                transaction.add_framework_info(name=framework[0], version=framework[1])

            # Also override the web transaction name to be the name of
            # the wrapped callable if not explicitly named, and we want
            # the default name to be that of the WSGI component for the
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

            return wrapped(*args, **kwargs)

        # Otherwise treat it as top level transaction. We have to though
        # look first to see whether the application name has been
        # overridden through the WSGI environ dictionary.

        def _args(environ, start_response, *args, **kwargs):
            return environ, start_response

        environ, start_response = _args(*args, **kwargs)

        target_application = application

        if "newrelic.app_name" in environ:
            app_name = environ["newrelic.app_name"]

            if ";" in app_name:
                app_names = [n.strip() for n in app_name.split(";")]
                app_name = app_names[0]
                target_application = application_instance(app_name)
                for altname in app_names[1:]:
                    target_application.link_to_application(altname)
            else:
                target_application = application_instance(app_name)
        else:
            # If application has an activate() method we assume it is an
            # actual application. Do this rather than check type so that
            # can easily mock it for testing.

            # FIXME Should this allow for multiple apps if a string.

            if not hasattr(application, "activate"):
                target_application = application_instance(application)

        # Now start recording the actual web transaction.
        transaction = WSGIWebTransaction(target_application, environ)
        transaction.__enter__()

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

        def _start_response(status, response_headers, *args):

            additional_headers = transaction.process_response(status, response_headers, *args)

            _write = start_response(status, response_headers + additional_headers, *args)

            def write(data):
                if not transaction._sent_start:
                    transaction._sent_start = time.time()
                result = _write(data)
                transaction._calls_write += 1
                try:
                    transaction._bytes_sent += len(data)
                except Exception:
                    pass
                transaction._sent_end = time.time()
                return result

            return write

        try:
            # Should always exist, but check as test harnesses may not
            # have it.

            if "wsgi.input" in environ:
                environ["wsgi.input"] = _WSGIInputWrapper(transaction, environ["wsgi.input"])

            with FunctionTrace(name="Application", group="Python/WSGI"):
                with FunctionTrace(name=callable_name(wrapped)):
                    if settings and settings.browser_monitoring.enabled and not transaction.autorum_disabled:
                        result = _WSGIApplicationMiddleware(wrapped, environ, _start_response, transaction)
                    else:
                        result = wrapped(environ, _start_response)

        except:  # Catch all
            transaction.__exit__(*sys.exc_info())
            raise

        return _WSGIApplicationIterable(transaction, result)

    return FunctionWrapper(wrapped, _nr_wsgi_application_wrapper_)


def wsgi_application(application=None, name=None, group=None, framework=None):
    return functools.partial(
        WSGIApplicationWrapper, application=application, name=name, group=group, framework=framework
    )


def wrap_wsgi_application(module, object_path, application=None, name=None, group=None, framework=None):
    wrap_object(module, object_path, WSGIApplicationWrapper, (application, name, group, framework))
