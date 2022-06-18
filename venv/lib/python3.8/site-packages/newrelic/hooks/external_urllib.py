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

def _nr_wrapper_factory(bind_params_fn, library):
    # Wrapper functions will be similar for monkeypatching the different
    # urllib functions and methods, so a factory function to create them is
    # used to reduce repetitiveness.

    # Parameters:
    #
    # bind_params_fn: Function that returns the URL.
    # library: String. The library name to be used for display in the UI
    # by ExternalTrace.

    def _nr_wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        url = bind_params_fn(*args, **kwargs)

        details = urlparse.urlparse(url)

        if details.hostname is None:
            return wrapped(*args, **kwargs)

        with ExternalTrace(library, url):
            return wrapped(*args, **kwargs)

    return _nr_wrapper

def bind_params_urlretrieve(url, *args, **kwargs):
    return url

def bind_params_open(fullurl, *args, **kwargs):

    if isinstance(fullurl, six.string_types):
        return fullurl
    else:
        return fullurl.get_full_url()

def instrument(module):

    if hasattr(module, 'urlretrieve'):

        _nr_wrapper_urlretrieve_ = _nr_wrapper_factory(
                bind_params_urlretrieve, 'urllib')

        wrap_function_wrapper(module, 'urlretrieve', _nr_wrapper_urlretrieve_)

    if hasattr(module, 'URLopener'):

        _nr_wrapper_url_opener_open_ = _nr_wrapper_factory(
                bind_params_open, 'urllib')

        wrap_function_wrapper(module, 'URLopener.open',
                _nr_wrapper_url_opener_open_)

    if hasattr(module, 'OpenerDirector'):

        _nr_wrapper_opener_director_open_ = _nr_wrapper_factory(
                bind_params_open, 'urllib2')

        wrap_function_wrapper(module, 'OpenerDirector.open',
                _nr_wrapper_opener_director_open_)
