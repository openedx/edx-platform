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

"""Instrumentation for the Cornice REST library for Pyramid.

"""

import functools

from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (function_wrapper,
        wrap_function_wrapper)

module_cornice_service = None

@function_wrapper
def wrapper_Resource_method(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    transaction.set_transaction_name(name)

    with FunctionTrace(name):
        return wrapped(*args, **kwargs)

def wrapper_Resource(view):
    @function_wrapper
    def _wrapper_Resource(wrapped, instance, args, kwargs):
        ob = wrapped(*args, **kwargs)
        method = getattr(ob, view)
        setattr(ob, view, wrapper_Resource_method(method))
        return ob
    return _wrapper_Resource

def wrapper_decorate_view(wrapped, instance, args, kwargs):
    def _bind_params(view, args, method, *other_args, **other_kwargs):
        return view, args, method

    _view, _args, _method = _bind_params(*args, **kwargs)

    if 'klass' in _args and not callable(_view):
        if module_cornice_service.is_string(_view):
            _klass = _args['klass']
            _args = dict(_args)
            _args['klass'] = wrapper_Resource(_view)(_klass)
            return wrapped(_view, _args, _method)

    # For Cornice 0.17 or older we need to fixup the fact that they do
    # not copy the wrapped view attributes to the wrapper it returns.
    # This is only needed where the view is not a string.

    wrapper = wrapped(*args, **kwargs)

    if not module_cornice_service.is_string(_view):
        if wrapper.__name__ != _view.__name__:
            return functools.wraps(_view)(wrapper)

    return wrapper

def instrument_cornice_service(module):
    global module_cornice_service
    module_cornice_service = module

    wrap_function_wrapper(module, 'decorate_view', wrapper_decorate_view)
