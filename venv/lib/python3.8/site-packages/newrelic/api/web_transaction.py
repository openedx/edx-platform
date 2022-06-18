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
import time
import logging
import warnings

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from newrelic.api.application import Application, application_instance
from newrelic.api.transaction import Transaction, current_transaction

from newrelic.common.async_proxy import async_proxy, TransactionContext
from newrelic.common.encoding_utils import (obfuscate, json_encode,
        decode_newrelic_header, ensure_str)

from newrelic.core.attribute import create_attributes, process_user_attribute
from newrelic.core.attribute_filter import DST_BROWSER_MONITORING, DST_NONE

from newrelic.packages import six

from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object

_logger = logging.getLogger(__name__)

_js_agent_header_fragment = '<script type="text/javascript">%s</script>'
_js_agent_footer_fragment = '<script type="text/javascript">'\
                            'window.NREUM||(NREUM={});NREUM.info=%s</script>'

# Seconds since epoch for Jan 1 2000
JAN_1_2000 = time.mktime((2000, 1, 1, 0, 0, 0, 0, 0, 0))
MICROSECOND_MIN = JAN_1_2000 * 1000000.0
MILLISECOND_MIN = JAN_1_2000 * 1000.0


def _parse_time_stamp(time_stamp):
    """
    Converts time_stamp to seconds. Input can be microseconds,
    milliseconds or seconds

    Divide the timestamp by the highest resolution divisor. If
    the result is older than Jan 1 2000, then pick a lower
    resolution divisor and repeat.  It is safe to assume no
    requests were queued for more than 10 years.

    """

    now = time.time()

    if time_stamp > MICROSECOND_MIN:
        divisor = 1000000.0
    elif time_stamp > MILLISECOND_MIN:
        divisor = 1000.0
    elif time_stamp > JAN_1_2000:
        divisor = 1.0
    else:
        return 0.0

    converted_time = time_stamp / divisor

    # If queue_start is in the future, return 0.0.
    if converted_time > now:
        return 0.0

    return converted_time


TRUE_VALUES = {'on', 'true', '1'}
FALSE_VALUES = {'off', 'false', '0'}


def _lookup_environ_setting(environ, name, default=False):
    if name not in environ:
        return default

    flag = environ[name]

    if isinstance(flag, six.string_types):
        flag = flag.lower()

        if flag in TRUE_VALUES:
            return True
        elif flag in FALSE_VALUES:
            return False

    return flag


def _parse_synthetics_header(header):
    # Return a dictionary of values from Synthetics header
    # Returns empty dict, if version is not supported.

    synthetics = {}
    version = None

    try:
        if len(header) > 0:
            version = int(header[0])

        if version == 1:
            synthetics['version'] = version
            synthetics['account_id'] = int(header[1])
            synthetics['resource_id'] = header[2]
            synthetics['job_id'] = header[3]
            synthetics['monitor_id'] = header[4]
    except Exception:
        return

    return synthetics


def _remove_query_string(url):
    url = ensure_str(url)
    out = urlparse.urlsplit(url)
    return urlparse.urlunsplit((out.scheme, out.netloc, out.path, '', ''))


def _is_websocket(environ):
    return environ.get('HTTP_UPGRADE', '').lower() == 'websocket'


class WebTransaction(Transaction):
    unicode_error_reported = False
    QUEUE_TIME_HEADERS = ('x-request-start', 'x-queue-start')

    def __init__(self, application, name, group=None,
            scheme=None, host=None, port=None, request_method=None,
            request_path=None, query_string=None, headers=None,
            enabled=None):

        super(WebTransaction, self).__init__(application, enabled)

        # Flags for tracking whether RUM header and footer have been
        # generated.

        self.rum_header_generated = False
        self.rum_footer_generated = False

        if not self.enabled:
            return

        # Inputs
        self._request_uri = request_path
        self._request_method = request_method
        self._request_scheme = scheme
        self._request_host = host
        self._request_params = {}
        self._request_headers = {}

        try:
            self._port = int(port)
        except Exception:
            self._port = None

        # Response
        self._response_headers = {}
        self._response_code = None

        if headers is not None:
            try:
                headers = headers.items()
            except Exception:
                pass

            for k, v in headers:
                k = ensure_str(k)
                if k is not None:
                    self._request_headers[k.lower()] = v

        # Capture query request string parameters, unless we're in
        # High Security Mode.
        if query_string and not self._settings.high_security:
            query_string = ensure_str(query_string)
            try:
                params = urlparse.parse_qs(
                        query_string,
                        keep_blank_values=True)
                self._request_params.update(params)
            except Exception:
                pass

        self._process_queue_time()
        self._process_synthetics_header()
        self._process_context_headers()

        if name is not None:
            self.set_transaction_name(name, group, priority=1)
        elif request_path is not None:
            self.set_transaction_name(request_path, 'Uri', priority=1)

    def _process_queue_time(self):
        for queue_time_header in self.QUEUE_TIME_HEADERS:
            value = self._request_headers.get(queue_time_header)
            if not value:
                continue
            value = ensure_str(value)

            try:
                if value.startswith('t='):
                    self.queue_start = _parse_time_stamp(float(value[2:]))
                else:
                    self.queue_start = _parse_time_stamp(float(value))
            except Exception:
                pass

            if self.queue_start > 0.0:
                break

    def _process_synthetics_header(self):
        # Check for Synthetics header

        settings = self._settings

        if settings.synthetics.enabled and \
                settings.trusted_account_ids and \
                settings.encoding_key:

            encoded_header = self._request_headers.get('x-newrelic-synthetics')
            encoded_header = encoded_header and ensure_str(encoded_header)
            if not encoded_header:
                return

            decoded_header = decode_newrelic_header(
                    encoded_header,
                    settings.encoding_key)
            synthetics = _parse_synthetics_header(decoded_header)

            if synthetics and \
                    synthetics['account_id'] in \
                    settings.trusted_account_ids:

                # Save obfuscated header, because we will pass it along
                # unchanged in all external requests.

                self.synthetics_header = encoded_header
                self.synthetics_resource_id = synthetics['resource_id']
                self.synthetics_job_id = synthetics['job_id']
                self.synthetics_monitor_id = synthetics['monitor_id']

    def _process_context_headers(self):
        # Process the New Relic cross process ID header and extract
        # the relevant details.
        if self._settings.distributed_tracing.enabled:
            self.accept_distributed_trace_headers(self._request_headers)
        else:
            client_cross_process_id = \
                    self._request_headers.get('x-newrelic-id')
            txn_header = self._request_headers.get('x-newrelic-transaction')
            self._process_incoming_cat_headers(client_cross_process_id,
                    txn_header)

    def process_response(self, status_code, response_headers):
        """Processes response status and headers, extracting any
        details required and returning a set of additional headers
        to merge into that being returned for the web transaction.

        """

        if not self.enabled:
            return []

        # Extract response headers
        if response_headers:
            try:
                response_headers = response_headers.items()
            except Exception:
                pass

            for header, value in response_headers:
                header = ensure_str(header)
                if header is not None:
                    self._response_headers[header.lower()] = value

        try:
            self._response_code = int(status_code)

            # If response code is 304 do not insert CAT headers. See:
            # https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.3.5
            if self._response_code == 304:
                return []
        except Exception:
            pass

        if self.client_cross_process_id is None:
            return []

        # Generate CAT response headers
        try:
            read_length = int(self._request_headers.get('content-length'))
        except Exception:
            read_length = -1

        return self._generate_response_headers(read_length)

    def _update_agent_attributes(self):
        if 'accept' in self._request_headers:
            self._add_agent_attribute('request.headers.accept',
                    self._request_headers['accept'])
        try:
            content_length = int(self._request_headers['content-length'])
            self._add_agent_attribute('request.headers.contentLength',
                    content_length)
        except:
            pass
        if 'content-type' in self._request_headers:
            self._add_agent_attribute('request.headers.contentType',
                    self._request_headers['content-type'])
        if 'host' in self._request_headers:
            self._add_agent_attribute('request.headers.host',
                    self._request_headers['host'])
        if 'referer' in self._request_headers:
            self._add_agent_attribute('request.headers.referer',
                    _remove_query_string(self._request_headers['referer']))
        if 'user-agent' in self._request_headers:
            self._add_agent_attribute('request.headers.userAgent',
                    self._request_headers['user-agent'])
        if self._request_method:
            self._add_agent_attribute('request.method', self._request_method)
        if self._request_uri:
            self._add_agent_attribute('request.uri', self._request_uri)
        try:
            content_length = int(self._response_headers['content-length'])
            self._add_agent_attribute('response.headers.contentLength',
                    content_length)
        except:
            pass
        if 'content-type' in self._response_headers:
            self._add_agent_attribute('response.headers.contentType',
                    self._response_headers['content-type'])
        if self._response_code is not None:
            self._add_agent_attribute('response.status',
                    str(self._response_code))

        return super(WebTransaction, self)._update_agent_attributes()

    def browser_timing_header(self):
        """Returns the JavaScript header to be included in any HTML
        response to perform real user monitoring. This function returns
        the header as a native Python string. In Python 2 native strings
        are stored as bytes. In Python 3 native strings are stored as
        unicode.

        """

        if not self.enabled:
            return ''

        if self._state != self.STATE_RUNNING:
            return ''

        if self.background_task:
            return ''

        if self.ignore_transaction:
            return ''

        if not self._settings:
            return ''

        if not self._settings.browser_monitoring.enabled:
            return ''

        if not self._settings.license_key:
            return ''

        # Don't return the header a second time if it has already
        # been generated.

        if self.rum_header_generated:
            return ''

        # Requirement is that the first 13 characters of the account
        # license key is used as the key when obfuscating values for
        # the RUM footer. Will not be able to perform the obfuscation
        # if license key isn't that long for some reason.

        if len(self._settings.license_key) < 13:
            return ''

        # Return the RUM header only if the agent received a valid value
        # for js_agent_loader from the data collector. The data
        # collector is not meant to send a non empty value for the
        # js_agent_loader value if browser_monitoring.loader is set to
        # 'none'.

        if self._settings.js_agent_loader:
            header = _js_agent_header_fragment % self._settings.js_agent_loader

            # To avoid any issues with browser encodings, we will make sure
            # that the javascript we inject for the browser agent is ASCII
            # encodable. Since we obfuscate all agent and user attributes, and
            # the transaction name with base 64 encoding, this will preserve
            # those strings, if they have values outside of the ASCII character
            # set. In the case of Python 2, we actually then use the encoded
            # value as we need a native string, which for Python 2 is a byte
            # string. If encoding as ASCII fails we will return an empty
            # string.

            try:
                if six.PY2:
                    header = header.encode('ascii')
                else:
                    header.encode('ascii')

            except UnicodeError:
                if not WebTransaction.unicode_error_reported:
                    _logger.error('ASCII encoding of js-agent-header failed.',
                            header)
                    WebTransaction.unicode_error_reported = True

                header = ''

        else:
            header = ''

        # We remember if we have returned a non empty string value and
        # if called a second time we will not return it again. The flag
        # will also be used to check whether the footer should be
        # generated.

        if header:
            self.rum_header_generated = True

        return header

    def browser_timing_footer(self):
        """Returns the JavaScript footer to be included in any HTML
        response to perform real user monitoring. This function returns
        the footer as a native Python string. In Python 2 native strings
        are stored as bytes. In Python 3 native strings are stored as
        unicode.

        """

        if not self.enabled:
            return ''

        if self._state != self.STATE_RUNNING:
            return ''

        if self.ignore_transaction:
            return ''

        # Only generate a footer if the header had already been
        # generated and we haven't already generated the footer.

        if not self.rum_header_generated:
            return ''

        if self.rum_footer_generated:
            return ''

        # Make sure we freeze the path.

        self._freeze_path()

        # When obfuscating values for the footer, we only use the
        # first 13 characters of the account license key.

        obfuscation_key = self._settings.license_key[:13]

        attributes = {}

        user_attributes = {}
        for attr in self.user_attributes:
            if attr.destinations & DST_BROWSER_MONITORING:
                user_attributes[attr.name] = attr.value

        if user_attributes:
            attributes['u'] = user_attributes

        request_parameters = self.request_parameters
        request_parameter_attributes = self.filter_request_parameters(
                request_parameters)
        agent_attributes = {}
        for attr in request_parameter_attributes:
            if attr.destinations & DST_BROWSER_MONITORING:
                agent_attributes[attr.name] = attr.value

        if agent_attributes:
            attributes['a'] = agent_attributes

        # create the data structure that pull all our data in

        footer_data = self.browser_monitoring_intrinsics(obfuscation_key)

        if attributes:
            attributes = obfuscate(json_encode(attributes), obfuscation_key)
            footer_data['atts'] = attributes

        footer = _js_agent_footer_fragment % json_encode(footer_data)

        # To avoid any issues with browser encodings, we will make sure that
        # the javascript we inject for the browser agent is ASCII encodable.
        # Since we obfuscate all agent and user attributes, and the transaction
        # name with base 64 encoding, this will preserve those strings, if
        # they have values outside of the ASCII character set.
        # In the case of Python 2, we actually then use the encoded value
        # as we need a native string, which for Python 2 is a byte string.
        # If encoding as ASCII fails we will return an empty string.

        try:
            if six.PY2:
                footer = footer.encode('ascii')
            else:
                footer.encode('ascii')

        except UnicodeError:
            if not WebTransaction.unicode_error_reported:
                _logger.error('ASCII encoding of js-agent-footer failed.',
                        footer)
                WebTransaction.unicode_error_reported = True

            footer = ''

        # We remember if we have returned a non empty string value and
        # if called a second time we will not return it again.

        if footer:
            self.rum_footer_generated = True

        return footer

    def browser_monitoring_intrinsics(self, obfuscation_key):
        txn_name = obfuscate(self.path, obfuscation_key)

        queue_start = self.queue_start or self.start_time
        start_time = self.start_time
        end_time = time.time()

        queue_duration = int((start_time - queue_start) * 1000)
        request_duration = int((end_time - start_time) * 1000)

        intrinsics = {
            "beacon": self._settings.beacon,
            "errorBeacon": self._settings.error_beacon,
            "licenseKey": self._settings.browser_key,
            "applicationID": self._settings.application_id,
            "transactionName": txn_name,
            "queueTime": queue_duration,
            "applicationTime": request_duration,
            "agent": self._settings.js_agent_file,
        }

        if self._settings.browser_monitoring.ssl_for_http is not None:
            ssl_for_http = self._settings.browser_monitoring.ssl_for_http
            intrinsics['sslForHttp'] = ssl_for_http

        return intrinsics


class WSGIHeaderProxy(object):
    def __init__(self, environ):
        self.environ = environ
        self.length = None

    @staticmethod
    def _to_wsgi(key):
        key = key.upper()
        if key == 'CONTENT-LENGTH':
            return 'CONTENT_LENGTH'
        elif key == 'CONTENT-TYPE':
            return 'CONTENT_TYPE'
        return 'HTTP_' + key.replace('-', '_')

    @staticmethod
    def _from_wsgi(key):
        key = key.lower()
        return key[5:].replace('_', '-')

    def __getitem__(self, key):
        wsgi_key = self._to_wsgi(key)
        return self.environ[wsgi_key]

    def __iter__(self):
        for key in self.environ:
            if key == 'CONTENT_LENGTH':
                yield 'content-length', self.environ['CONTENT_LENGTH']
            elif key == 'CONTENT_TYPE':
                yield 'content-type', self.environ['CONTENT_TYPE']
            elif key == 'HTTP_CONTENT_LENGTH' or key == 'HTTP_CONTENT_TYPE':
                # These keys are illegal and should be ignored
                continue
            elif key.startswith('HTTP_'):
                yield self._from_wsgi(key), self.environ[key]

    def __len__(self):
        if self.length is None:
            self.length = sum(1 for _ in iter(self))
        return self.length


class WSGIWebTransaction(WebTransaction):

    MOD_WSGI_HEADERS = ('mod_wsgi.request_start', 'mod_wsgi.queue_start')

    def __init__(self, application, environ):

        # The web transaction can be enabled/disabled by
        # the value of the variable "newrelic.enabled"
        # in the WSGI environ dictionary. We need to check
        # this before initialising the transaction as needs
        # to be passed in base class constructor. The
        # default is None, which would then result in the
        # base class making the decision based on whether
        # application or agent as a whole are enabled.

        enabled = _lookup_environ_setting(environ,
                'newrelic.enabled', None)

        # Initialise the common transaction base class.

        super(WSGIWebTransaction, self).__init__(
            application, name=None, port=environ.get('SERVER_PORT'),
            request_method=environ.get('REQUEST_METHOD'),
            query_string=environ.get('QUERY_STRING'),
            headers=iter(WSGIHeaderProxy(environ)),
            enabled=enabled)

        # Disable transactions for websocket connections.
        # Also disable autorum if this is a websocket. This is a good idea for
        # two reasons. First, RUM is unnecessary for websocket transactions
        # anyway. Secondly, due to a bug in the gevent-websocket (0.9.5)
        # package, if our _WSGIApplicationMiddleware is applied a websocket
        # connection cannot be made.

        if _is_websocket(environ):
            self.autorum_disabled = True
            self.enabled = False

        # Bail out if the transaction is running in a
        # disabled state.

        if not self.enabled:
            return

        # Will need to check the settings a number of times.

        settings = self._settings

        # Check for override settings from WSGI environ.

        self.background_task = _lookup_environ_setting(environ,
                'newrelic.set_background_task', False)

        self.ignore_transaction = _lookup_environ_setting(environ,
                'newrelic.ignore_transaction', False)
        self.suppress_apdex = _lookup_environ_setting(environ,
                'newrelic.suppress_apdex_metric', False)
        self.suppress_transaction_trace = _lookup_environ_setting(environ,
                'newrelic.suppress_transaction_trace', False)
        self.capture_params = _lookup_environ_setting(environ,
                'newrelic.capture_request_params',
                settings.capture_params)
        self.autorum_disabled = _lookup_environ_setting(environ,
                'newrelic.disable_browser_autorum',
                not settings.browser_monitoring.auto_instrument)

        # Make sure that if high security mode is enabled that
        # capture of request params is still being disabled.
        # No warning is issued for this in the logs because it
        # is a per request configuration and would create a lot
        # of noise.

        if settings.high_security:
            self.capture_params = False

        # LEGACY: capture_params = False
        #
        #    Don't add request parameters at all, which means they will not
        #    go through the AttributeFilter.
        if self.capture_params is False:
            self._request_params.clear()

        # Extract from the WSGI environ dictionary
        # details of the URL path. This will be set as
        # default path for the web transaction. This can
        # be overridden by framework to be more specific
        # to avoid metrics explosion problem resulting
        # from too many distinct URLs for same resource
        # due to use of REST style URL concepts or
        # otherwise.

        request_uri = environ.get('REQUEST_URI', None)

        if request_uri is None:
            # The gunicorn WSGI server uses RAW_URI instead
            # of the more typical REQUEST_URI used by Apache
            # and other web servers.

            request_uri = environ.get('RAW_URI', None)

        script_name = environ.get('SCRIPT_NAME', None)
        path_info = environ.get('PATH_INFO', None)

        self._request_uri = request_uri

        if self._request_uri is not None:
            # Need to make sure we drop off any query string
            # arguments on the path if we have to fallback
            # to using the original REQUEST_URI. Can't use
            # attribute access on result as only support for
            # Python 2.5+.

            self._request_uri = urlparse.urlparse(self._request_uri)[2]

        if script_name is not None or path_info is not None:
            if path_info is None:
                path = script_name
            elif script_name is None:
                path = path_info
            else:
                path = script_name + path_info

            self.set_transaction_name(path, 'Uri', priority=1)

            if self._request_uri is None:
                self._request_uri = path
        else:
            if self._request_uri is not None:
                self.set_transaction_name(self._request_uri, 'Uri', priority=1)

        # mod_wsgi sets its own distinct variables for queue time
        # automatically. Initially it set mod_wsgi.queue_start,
        # which equated to when Apache first accepted the
        # request. This got changed to mod_wsgi.request_start
        # however, and mod_wsgi.queue_start was instead used
        # just for when requests are to be queued up for the
        # daemon process and corresponded to the point at which
        # they are being proxied, after Apache does any
        # authentication etc. We check for both so older
        # versions of mod_wsgi will still work, although we
        # don't try and use the fact that it is possible to
        # distinguish the two points and just pick up the
        # earlier of the two.
        for queue_time_header in self.MOD_WSGI_HEADERS:
            if self.queue_start > 0.0:
                break

            value = environ.get(queue_time_header)
            if not value:
                continue

            try:
                if value.startswith('t='):
                    try:
                        self.queue_start = _parse_time_stamp(float(value[2:]))
                    except Exception:
                        pass
                else:
                    try:
                        self.queue_start = _parse_time_stamp(float(value))
                    except Exception:
                        pass

            except Exception:
                pass

    def __exit__(self, exc, value, tb):
        self.record_custom_metric('Python/WSGI/Input/Bytes',
                            self._bytes_read)
        self.record_custom_metric('Python/WSGI/Input/Time',
                            self.read_duration)
        self.record_custom_metric('Python/WSGI/Input/Calls/read',
                            self._calls_read)
        self.record_custom_metric('Python/WSGI/Input/Calls/readline',
                            self._calls_readline)
        self.record_custom_metric('Python/WSGI/Input/Calls/readlines',
                            self._calls_readlines)

        self.record_custom_metric('Python/WSGI/Output/Bytes',
                            self._bytes_sent)
        self.record_custom_metric('Python/WSGI/Output/Time',
                            self.sent_duration)
        self.record_custom_metric('Python/WSGI/Output/Calls/yield',
                            self._calls_yield)
        self.record_custom_metric('Python/WSGI/Output/Calls/write',
                            self._calls_write)

        return super(WSGIWebTransaction, self).__exit__(exc, value, tb)

    def _update_agent_attributes(self):
        # Add WSGI agent attributes
        if self.read_duration != 0:
            self._add_agent_attribute('wsgi.input.seconds',
                    self.read_duration)
        if self._bytes_read != 0:
            self._add_agent_attribute('wsgi.input.bytes',
                    self._bytes_read)
        if self._calls_read != 0:
            self._add_agent_attribute('wsgi.input.calls.read',
                    self._calls_read)
        if self._calls_readline != 0:
            self._add_agent_attribute('wsgi.input.calls.readline',
                    self._calls_readline)
        if self._calls_readlines != 0:
            self._add_agent_attribute('wsgi.input.calls.readlines',
                    self._calls_readlines)

        if self.sent_duration != 0:
            self._add_agent_attribute('wsgi.output.seconds',
                    self.sent_duration)
        if self._bytes_sent != 0:
            self._add_agent_attribute('wsgi.output.bytes',
                    self._bytes_sent)
        if self._calls_write != 0:
            self._add_agent_attribute('wsgi.output.calls.write',
                    self._calls_write)
        if self._calls_yield != 0:
            self._add_agent_attribute('wsgi.output.calls.yield',
                    self._calls_yield)

        return super(WSGIWebTransaction, self)._update_agent_attributes()

    def process_response(self, status, response_headers, *args):
        """Processes response status and headers, extracting any
        details required and returning a set of additional headers
        to merge into that being returned for the web transaction.

        """

        # Set our internal response code based on WSGI status.
        # Per spec, it is expected that this is a string. If this is not
        # the case, skip setting the internal response code as we cannot
        # make the determination. (An integer 200 for example when passed
        # would raise as a 500 for WSGI applications).

        try:
            status = status.split(' ', 1)[0]
        except Exception:
            status = None

        return super(WSGIWebTransaction, self).process_response(
                status, response_headers)


def WebTransactionWrapper(wrapped, application=None, name=None, group=None,
        scheme=None, host=None, port=None, request_method=None,
        request_path=None, query_string=None, headers=None):

    def wrapper(wrapped, instance, args, kwargs):

        if type(application) != Application:
            _application = application_instance(application)
        else:
            _application = application

        if callable(name):
            if instance is not None:
                _name = name(instance, *args, **kwargs)
            else:
                _name = name(*args, **kwargs)
        elif name is None:
            _name = callable_name(wrapped)
        else:
            _name = name

        if callable(group):
            if instance is not None:
                _group = group(instance, *args, **kwargs)
            else:
                _group = group(*args, **kwargs)
        else:
            _group = group

        if callable(scheme):
            if instance is not None:
                _scheme = scheme(instance, *args, **kwargs)
            else:
                _scheme = scheme(*args, **kwargs)
        else:
            _scheme = scheme

        if callable(host):
            if instance is not None:
                _host = host(instance, *args, **kwargs)
            else:
                _host = host(*args, **kwargs)
        else:
            _host = host

        if callable(port):
            if instance is not None:
                _port = port(instance, *args, **kwargs)
            else:
                _port = port(*args, **kwargs)
        else:
            _port = port

        if callable(request_method):
            if instance is not None:
                _request_method = request_method(instance, *args, **kwargs)
            else:
                _request_method = request_method(*args, **kwargs)
        else:
            _request_method = request_method

        if callable(request_path):
            if instance is not None:
                _request_path = request_path(instance, *args, **kwargs)
            else:
                _request_path = request_path(*args, **kwargs)
        else:
            _request_path = request_path

        if callable(query_string):
            if instance is not None:
                _query_string = query_string(instance, *args, **kwargs)
            else:
                _query_string = query_string(*args, **kwargs)
        else:
            _query_string = query_string

        if callable(headers):
            if instance is not None:
                _headers = headers(instance, *args, **kwargs)
            else:
                _headers = headers(*args, **kwargs)
        else:
            _headers = headers


        proxy = async_proxy(wrapped)

        def create_transaction(transaction):
            if transaction:
                return None
            return WebTransaction( _application, _name, _group,
                    _scheme, _host, _port, _request_method,
                    _request_path, _query_string, _headers)

        if proxy:
            context_manager = TransactionContext(create_transaction)
            return proxy(wrapped(*args, **kwargs), context_manager)

        transaction = WebTransaction(
                _application, _name, _group, _scheme, _host, _port,
                _request_method, _request_path, _query_string, _headers)

        transaction = create_transaction(current_transaction(active_only=False))

        if not transaction:
            return wrapped(*args, **kwargs)

        with transaction:
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, wrapper)


def web_transaction(application=None, name=None, group=None,
        scheme=None, host=None, port=None, request_method=None,
        request_path=None, query_string=None, headers=None):

    return functools.partial(WebTransactionWrapper,
            application=application, name=name, group=group,
            scheme=scheme, host=host, port=port, request_method=request_method,
            request_path=request_path, query_string=query_string,
            headers=headers)


def wrap_web_transaction(module, object_path,
        application=None, name=None, group=None,
        scheme=None, host=None, port=None, request_method=None,
        request_path=None, query_string=None, headers=None):

    return wrap_object(module, object_path, WebTransactionWrapper,
            (application, name, group, scheme, host, port, request_method,
            request_path, query_string, headers))
