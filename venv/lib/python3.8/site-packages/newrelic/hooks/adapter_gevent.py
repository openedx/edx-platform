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

from newrelic.common.object_wrapper import wrap_in_function
from newrelic.api.wsgi_application import WSGIApplicationWrapper

def instrument_gevent_wsgi(module):

    def wrapper_WSGIServer___init__(*args, **kwargs):
        def _bind_params(self, listener, application, *args, **kwargs):
            return self, listener, application, args, kwargs

        self, listener, application, _args, _kwargs = _bind_params(
                *args, **kwargs)

        application = WSGIApplicationWrapper(application)

        _args = (self, listener, application) + _args

        return _args, _kwargs

    wrap_in_function(module, 'WSGIServer.__init__',
            wrapper_WSGIServer___init__)

def instrument_gevent_pywsgi(module):

    def wrapper_WSGIServer___init__(*args, **kwargs):
        def _bind_params(self, listener, application, *args, **kwargs):
            return self, listener, application, args, kwargs

        self, listener, application, _args, _kwargs = _bind_params(
                *args, **kwargs)

        application = WSGIApplicationWrapper(application)

        _args = (self, listener, application) + _args

        return _args, _kwargs

    wrap_in_function(module, 'WSGIServer.__init__',
            wrapper_WSGIServer___init__)
