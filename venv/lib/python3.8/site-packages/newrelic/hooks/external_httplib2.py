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

from newrelic.api.external_trace import wrap_external_trace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper


def _nr_wrapper_httplib2_endheaders_wrapper(*library_info):

    def _nr_wrapper_httplib2_endheaders_wrapper_inner(wrapped, instance,
            args, kwargs):

        def _connect_unbound(instance, *args, **kwargs):
            return instance

        if instance is None:
            instance = _connect_unbound(*args, **kwargs)

        connection = instance

        connection._nr_library_info = library_info
        return wrapped(*args, **kwargs)

    return _nr_wrapper_httplib2_endheaders_wrapper_inner


def instrument(module):

    wrap_function_wrapper(module, 'HTTPConnectionWithTimeout.endheaders',
            _nr_wrapper_httplib2_endheaders_wrapper('httplib2', 'http'))

    wrap_function_wrapper(module, 'HTTPSConnectionWithTimeout.endheaders',
            _nr_wrapper_httplib2_endheaders_wrapper('httplib2', 'https'))

    def url_request(connection, uri, *args, **kwargs):
        return uri

    wrap_external_trace(module, 'Http.request', 'httplib2', url_request)
