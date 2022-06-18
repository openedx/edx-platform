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

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import newrelic.packages.six as six

from newrelic.api.external_trace import ExternalTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper

def _nr_wrapper_opener_director_open_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    def _bind_params(fullurl, *args, **kwargs):
        if isinstance(fullurl, six.string_types):
            return fullurl
        else:
            return fullurl.get_full_url()

    url = _bind_params(*args, **kwargs)

    details = urlparse.urlparse(url)

    if details.hostname is None:
        return wrapped(*args, **kwargs)

    with ExternalTrace('urllib2', url):
        return wrapped(*args, **kwargs)

def instrument(module):

    if hasattr(module, 'OpenerDirector'):
        wrap_function_wrapper(module, 'OpenerDirector.open',
            _nr_wrapper_opener_director_open_)
