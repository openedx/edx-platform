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

import newrelic.api.transaction
import newrelic.api.transaction_name
import newrelic.api.function_trace
import newrelic.api.error_trace
import newrelic.api.object_wrapper
import newrelic.api.import_hook

from newrelic.api.time_trace import notice_error

def name_controller(self, environ, start_response):
    action = environ['pylons.routes_dict']['action']
    return "%s.%s" % (newrelic.api.object_wrapper.callable_name(self), action)

class capture_error(object):
    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None
        self.__instance = instance
        self.__wrapped = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self.__wrapped.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __call__(self, *args, **kwargs):
        current_transaction = newrelic.api.transaction.current_transaction()
        if current_transaction:
            webob_exc = newrelic.api.import_hook.import_module('webob.exc')
            try:
                return self.__wrapped(*args, **kwargs)
            except webob_exc.HTTPException:
                raise
            except:  # Catch all
                notice_error()
                raise
        else:
            return self.__wrapped(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.__wrapped, name)

def instrument(module):

    if module.__name__ == 'pylons.wsgiapp':
        newrelic.api.error_trace.wrap_error_trace(module, 'PylonsApp.__call__')

    elif module.__name__ == 'pylons.controllers.core':
        newrelic.api.transaction_name.wrap_transaction_name(
                module, 'WSGIController.__call__', name_controller)
        newrelic.api.function_trace.wrap_function_trace(
                module, 'WSGIController.__call__')

        def name_WSGIController_perform_call(self, func, args):
            return newrelic.api.object_wrapper.callable_name(func)

        newrelic.api.function_trace.wrap_function_trace(
                module, 'WSGIController._perform_call',
                name_WSGIController_perform_call)
        newrelic.api.object_wrapper.wrap_object(
                module, 'WSGIController._perform_call', capture_error)

    elif module.__name__ == 'pylons.templating':

        newrelic.api.function_trace.wrap_function_trace(module, 'render_genshi')
        newrelic.api.function_trace.wrap_function_trace(module, 'render_mako')
        newrelic.api.function_trace.wrap_function_trace(module, 'render_jinja2')
