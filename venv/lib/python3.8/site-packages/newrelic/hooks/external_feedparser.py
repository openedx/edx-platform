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

import sys
import types

import newrelic.packages.six as six

import newrelic.api.transaction
import newrelic.api.object_wrapper
import newrelic.api.external_trace

class capture_external_trace(object):

    def __init__(self, wrapped):
        newrelic.api.object_wrapper.update_wrapper(self, wrapped)
        self._nr_next_object = wrapped
        if not hasattr(self, '_nr_last_object'):
            self._nr_last_object = wrapped

    def __call__(self, url, *args, **kwargs):

        # The URL be a string or a file like object. Pass call
        # through if not a string.

        if not isinstance(url, six.string_types):
            return self._nr_next_object(url, *args, **kwargs)

        # Only then wrap the call if it looks like a URL. To
        # work that out need to first do some conversions of
        # accepted 'feed' formats to proper URL format.

        parsed_url = url

        if parsed_url.startswith('feed:http'):
            parsed_url = parsed_url[5:]
        elif parsed_url.startswith('feed:'):
            parsed_url = 'http:' + url[5:]

        if parsed_url.split(':')[0].lower() in ['http', 'https', 'ftp']:
            current_transaction = newrelic.api.transaction.current_transaction()
            if current_transaction:
                trace = newrelic.api.external_trace.ExternalTrace(
                        'feedparser', parsed_url, 'GET')
                context_manager = trace.__enter__()
                try:
                    result = self._nr_next_object(url, *args, **kwargs)
                except:  # Catch all
                    context_manager.__exit__(*sys.exc_info())
                    raise
                context_manager.__exit__(None, None, None)
                return result
            else:
                return self._nr_next_object(url, *args, **kwargs)
        else:
            return self._nr_next_object(url, *args, **kwargs)

    def __getattr__(self, name):
       return getattr(self._nr_next_object, name)

def instrument(module):
    newrelic.api.object_wrapper.wrap_object(
            module, 'parse', capture_external_trace)
