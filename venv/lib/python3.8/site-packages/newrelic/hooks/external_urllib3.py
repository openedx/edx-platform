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

from newrelic.api.external_trace import ExternalTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.hooks.external_httplib2 import (
    _nr_wrapper_httplib2_endheaders_wrapper)


def _nr_wrapper_make_request_(wrapped, instance, args, kwargs):

    def _bind_params(conn, method, url, *args, **kwargs):
        return "%s://%s:%s" % (instance.scheme, conn.host, conn.port)

    url_for_apm_ui = _bind_params(*args, **kwargs)

    with ExternalTrace('urllib3', url_for_apm_ui):
        return wrapped(*args, **kwargs)


def instrument_urllib3_connectionpool(module):
    wrap_function_wrapper(module, 'HTTPSConnectionPool._make_request',
            _nr_wrapper_make_request_)
    wrap_function_wrapper(module, 'HTTPConnectionPool._make_request',
            _nr_wrapper_make_request_)


def instrument_urllib3_connection(module):
    # Don't combine the instrument functions into a single function. Keep
    # the 'connect' monkey patch separate, because it is also used to patch
    # urllib3 within the requests package.

    wrap_function_wrapper(module, 'HTTPSConnection.endheaders',
        _nr_wrapper_httplib2_endheaders_wrapper('urllib3', 'https'))

    wrap_function_wrapper(module, 'HTTPConnection.endheaders',
        _nr_wrapper_httplib2_endheaders_wrapper('urllib3', 'http'))
