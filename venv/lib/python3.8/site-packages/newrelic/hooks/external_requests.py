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

import newrelic.api.external_trace

def instrument_requests_sessions(module):

    def url_request(obj, method, url, *args, **kwargs):
        return url

    def url_send(obj, request, *args, **kwargs):
        return request.url

    if hasattr(module.Session, 'send'):

        # Session.send() was introduced in v1.0.0. At the same time,
        # Session.request() was modified to use Session.send() underneath,
        # so if the version of Requests is >= 1.0.0, then we only need to
        # instrument Session.send().

        newrelic.api.external_trace.wrap_external_trace(
                module, 'Session.send', 'requests', url_send)

    else:

        # If Session.send() doesn't exist, then we are instrumenting
        # a version of Requests < 1.0.0, so we need to instrument
        # Session.request().

        if hasattr(module.Session, 'request'):
            newrelic.api.external_trace.wrap_external_trace(
                   module, 'Session.request', 'requests', url_request)

def instrument_requests_api(module):

    def url_request(method, url, *args, **kwargs):
        return url

    if hasattr(module, 'request'):

        newrelic.api.external_trace.wrap_external_trace(
               module, 'request', 'requests', url_request)
