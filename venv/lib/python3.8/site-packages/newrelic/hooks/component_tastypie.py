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

from newrelic.api.function_trace import FunctionTrace
from newrelic.api.object_wrapper import ObjectWrapper, callable_name
from newrelic.api.transaction import current_transaction
from newrelic.api.time_trace import notice_error
from newrelic.common.object_wrapper import wrap_function_wrapper


def _nr_wrap_handle_exception(wrapped, instance, args, kwargs):

    response = wrapped(*args, **kwargs)

    notice_error(status_code=response.status_code)

    return response


def outer_fn_wrapper(outer_fn, instance, args, kwargs):
    view_name = args[0]

    meta = getattr(instance, "_meta", None)

    if meta is None:
        group = 'Python/TastyPie/Api'
        name = instance.api_name
        callback = getattr(instance, 'top_level', None)
    elif meta.api_name is not None:
        group = 'Python/TastyPie/Api'
        name = '%s/%s/%s' % (meta.api_name, meta.resource_name, view_name)
        callback = getattr(instance, view_name, None)
    else:
        group = 'Python/TastyPie/Resource'
        name = '%s/%s' % (meta.resource_name, view_name)
        callback = getattr(instance, view_name, None)

    # Give preference to naming web transaction and trace node after
    # target callback, but fall back to abstract path if for some reason
    # we don't get a valid target callback.

    if callback is not None:
        name = callable_name(callback)
        group = None

    def inner_fn_wrapper(inner_fn, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None or name is None:
            return inner_fn(*args, **kwargs)

        transaction.set_transaction_name(name, group, priority=5)

        with FunctionTrace(name, group):
            # django's exception handling will record errors here
            return inner_fn(*args, **kwargs)

    result = outer_fn(*args, **kwargs)

    return ObjectWrapper(result, None, inner_fn_wrapper)


def instrument_tastypie_resources(module):
    _wrap_view = module.Resource.wrap_view
    module.Resource.wrap_view = ObjectWrapper(
            _wrap_view, None, outer_fn_wrapper)

    wrap_function_wrapper(module, 'Resource._handle_500',
            _nr_wrap_handle_exception)


def instrument_tastypie_api(module):
    _wrap_view = module.Api.wrap_view
    module.Api.wrap_view = ObjectWrapper(_wrap_view, None, outer_fn_wrapper)
