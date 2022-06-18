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

from newrelic.api.wsgi_application import WSGIApplicationWrapper
from newrelic.common.object_wrapper import wrap_out_function
from newrelic.common.coroutine import (is_coroutine_callable,
        is_asyncio_coroutine)


def is_coroutine(fn):
    return is_coroutine_callable(fn) or is_asyncio_coroutine(fn)


def _nr_wrapper_Application_wsgi_(application):
    # Normally Application.wsgi() returns a WSGI application, but in
    # some async frameworks a special class or coroutine is returned. We must
    # check for those cases and avoid insturmenting the coroutine or
    # specialized class.

    try:
        if 'tornado.web' in sys.modules:
            import tornado.web
            if isinstance(application, tornado.web.Application):
                return application
    except ImportError:
        pass

    if is_coroutine(application):
        return application
    elif (hasattr(application, '__call__') and
            is_coroutine(application.__call__)):
        return application
    else:
        return WSGIApplicationWrapper(application)


def instrument_gunicorn_app_base(module):
    wrap_out_function(module, 'Application.wsgi',
            _nr_wrapper_Application_wsgi_)
