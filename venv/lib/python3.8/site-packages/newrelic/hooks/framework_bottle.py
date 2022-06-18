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

"""Instrumentation module for Bottle framework.

"""

import functools

from newrelic.api.function_trace import (FunctionTrace, FunctionTraceWrapper,
        wrap_function_trace)
from newrelic.api.transaction import current_transaction
from newrelic.api.wsgi_application import wrap_wsgi_application
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (wrap_out_function,
        function_wrapper, ObjectProxy, wrap_object_attribute,
        wrap_function_wrapper)

module_bottle = None

def status_code(exc, value, tb):
    # The HTTPError class derives from HTTPResponse and so we do not
    # need to check for it seperately as isinstance() will pick it up.

    if isinstance(value, module_bottle.HTTPResponse):
        if hasattr(value, 'status_code'):
            return value.status_code
        elif hasattr(value, 'status'):
            return value.status
        elif hasattr(value, 'http_status_code'):
            return value.http_status_code

def should_ignore(exc, value, tb):
    if hasattr(module_bottle, 'RouteReset'):
        if isinstance(value, module_bottle.RouteReset):
            return True

@function_wrapper
def callback_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    # Needs to be at a higher priority so that error handler processing
    # below will not override the web transaction being named after the
    # actual request handler.

    transaction.set_transaction_name(name, priority=2)

    with FunctionTrace(name) as trace:
        try:
            return wrapped(*args, **kwargs)

        except:  # Catch all
            # In most cases this seems like it will never be invoked as
            # bottle will internally capture the exception before we
            # get a chance and rather than propagate the exception will
            # return it instead. This doesn't always seem to be the case
            # though when plugins are used, although that may depend on
            # the specific bottle version being used.
            trace.notice_error(status_code=status_code, ignore=should_ignore)
            raise

def output_wrapper_Bottle_match(result):
    callback, args = result
    return callback_wrapper(callback), args

def output_wrapper_Route_make_callback(callback):
    return callback_wrapper(callback)

class proxy_Bottle_error_handler(ObjectProxy):
    # This proxy wraps the error_handler attribute of the Bottle class.
    # The attribute is a dictionary of handlers for HTTP status codes.
    # We specifically override the get() method of the dictionary so
    # that we can determine if the dictionary actually held a handler
    # for a specific HTTP status code. If it didn't, we name the web
    # transaction based on the status code as a fallback if not already
    # set based on a specific request handler. Otherwise, if there was
    # an error handler we will name the web transaction after the error
    # handler instead if not already set based on a specific request
    # handler.

    def get(self, status, default=None):
        transaction = current_transaction()

        if transaction is None:
            return self.__wrapped__.get(status, default)

        handler = self.__wrapped__.get(status)

        if handler:
            name = callable_name(handler)
            transaction.set_transaction_name(name, priority=1)
            handler = FunctionTraceWrapper(handler, name=name)
        else:
            transaction.set_transaction_name(str(status),
                    group='StatusCode', priority=1)

        return handler or default

def wrapper_auth_basic(wrapped, instance, args, kwargs):
    # Bottle has a bug whereby functools.wraps() is not used on the
    # nested wrapper function in the implementation of auth_basic()
    # decorator. We apply it ourself to try and workaround the issue.
    # Note that this is dependent though on the agent having been
    # initialised before the auth_basic() decorator is used. The issue
    # exists in bottle up to version 0.12.3, but shouldn't matter that
    # we reapply wraps() even in newer versions which address issue.

    decorator = wrapped(*args, **kwargs)

    def _decorator(func):
        return functools.wraps(func)(decorator(func))

    return _decorator

def instrument_bottle(module):
    global module_bottle
    module_bottle = module

    framework_details = ('Bottle', getattr(module, '__version__'))

    if hasattr(module.Bottle, 'wsgi'): # version >= 0.9
        wrap_wsgi_application(module, 'Bottle.wsgi',
                framework=framework_details)
    elif hasattr(module.Bottle, '__call__'): # version < 0.9
        wrap_wsgi_application(module, 'Bottle.__call__',
                framework=framework_details)

    if (hasattr(module, 'Route') and
            hasattr(module.Route, '_make_callback')): # version >= 0.10
        wrap_out_function(module, 'Route._make_callback',
                output_wrapper_Route_make_callback)
    elif hasattr(module.Bottle, '_match'): # version >= 0.9
        wrap_out_function(module, 'Bottle._match',
                output_wrapper_Bottle_match)
    elif hasattr(module.Bottle, 'match_url'): # version < 0.9
        wrap_out_function(module, 'Bottle.match_url',
                output_wrapper_Bottle_match)

    wrap_object_attribute(module, 'Bottle.error_handler',
            proxy_Bottle_error_handler)

    if hasattr(module, 'auth_basic'):
        wrap_function_wrapper(module, 'auth_basic', wrapper_auth_basic)

    if hasattr(module, 'SimpleTemplate'):
        wrap_function_trace(module, 'SimpleTemplate.render')

    if hasattr(module, 'MakoTemplate'):
        wrap_function_trace(module, 'MakoTemplate.render')

    if hasattr(module, 'CheetahTemplate'):
        wrap_function_trace(module, 'CheetahTemplate.render')

    if hasattr(module, 'Jinja2Template'):
        wrap_function_trace(module, 'Jinja2Template.render')

    if hasattr(module, 'SimpleTALTemplate'):
        wrap_function_trace(module, 'SimpleTALTemplate.render')
