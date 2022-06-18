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

from newrelic.common.object_wrapper import (wrap_function_wrapper,
        function_wrapper)
from newrelic.api.transaction import current_transaction
from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_names import callable_name


def _nr_wrapper_APIView_dispatch_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    def _args(request, *args, **kwargs):
        return request

    view = instance
    request = _args(*args, **kwargs)
    request_method = request.method.lower()

    if request_method in view.http_method_names:
        handler = getattr(view, request_method, view.http_method_not_allowed)
    else:
        handler = view.http_method_not_allowed

    view_func_callable_name = getattr(view, '_nr_view_func_callable_name',
            None)
    if view_func_callable_name:
        if handler == view.http_method_not_allowed:
            name = '%s.%s' % (view_func_callable_name,
                    'http_method_not_allowed')
        else:
            name = '%s.%s' % (view_func_callable_name, request_method)
    else:
        name = callable_name(handler)

    transaction.set_transaction_name(name)

    # catch exceptions handled by view.handle_exception
    view.handle_exception = _nr_wrapper_APIView_handle_exception_(
            view.handle_exception, request)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)


def _nr_wrapper_APIView_handle_exception_(handler, request):
    @function_wrapper
    def _handle_exception_wrapper(wrapped, instance, args, kwargs):
        request._nr_exc_info = sys.exc_info()
        return wrapped(*args, **kwargs)
    return _handle_exception_wrapper(handler)


@function_wrapper
def _nr_wrapper_api_view_decorator_(wrapped, instance, args, kwargs):
    def _bind_params(func, *args, **kwargs):
        return func

    func = _bind_params(*args, **kwargs)
    view = wrapped(*args, **kwargs)

    view.cls._nr_view_func_callable_name = callable_name(func)

    return view


def _nr_wrapper_api_view_(wrapped, instance, args, kwargs):
    decorator = wrapped(*args, **kwargs)
    decorator = _nr_wrapper_api_view_decorator_(decorator)
    return decorator


def instrument_rest_framework_views(module):
    wrap_function_wrapper(module, 'APIView.dispatch',
            _nr_wrapper_APIView_dispatch_)


def instrument_rest_framework_decorators(module):
    wrap_function_wrapper(module, 'api_view',
            _nr_wrapper_api_view_)
