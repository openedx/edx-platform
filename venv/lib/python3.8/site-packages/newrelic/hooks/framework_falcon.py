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
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (wrap_function_wrapper,
        function_wrapper)
from newrelic.api.transaction import current_transaction
from newrelic.api.time_trace import notice_error
from newrelic.api.wsgi_application import wrap_wsgi_application
from newrelic.api.function_trace import function_trace


def _bind_handle_exception_v1(ex, req, resp, *args, **kwargs):
    return resp


def _bind_handle_exception_v2(req, resp, *args, **kwargs):
    return resp


def build_wrap_handle_exception(bind_handle_exception):
    def wrap_handle_exception(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        name = callable_name(wrapped)
        transaction.set_transaction_name(name, priority=1)

        result = wrapped(*args, **kwargs)
        if result:
            exc_info = sys.exc_info()
            try:
                resp = bind_handle_exception(*args, **kwargs)
                response_code = int(resp.status.split()[0])
                notice_error(error=exc_info, status_code=response_code)
            except:
                notice_error(exc_info)
            finally:
                exc_info = None

        return result

    return wrap_handle_exception


@function_wrapper
def method_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)
    transaction.set_transaction_name(name, priority=2)

    traced_method = function_trace(name=name)(wrapped)
    return traced_method(*args, **kwargs)


def wrap_responder(wrapped, instance, args, kwargs):
    method_map = wrapped(*args, **kwargs)
    for key, method in method_map.items():
        method_map[key] = method_wrapper(method)

    return method_map


def framework_details():
    import falcon
    return ('Falcon', getattr(falcon, '__version__', None))


def instrument_falcon_api(module):
    framework = framework_details()

    major_version = int(framework[1].split('.')[0])
    if major_version < 2:
        wrap_handle_exception = \
                build_wrap_handle_exception(_bind_handle_exception_v1)
    else:
        wrap_handle_exception = \
                build_wrap_handle_exception(_bind_handle_exception_v2)

    wrap_wsgi_application(module, 'API.__call__',
            framework=framework)

    wrap_function_wrapper(module, 'API._handle_exception',
            wrap_handle_exception)


def instrument_falcon_app(module):
    framework = framework_details()

    wrap_handle_exception = \
            build_wrap_handle_exception(_bind_handle_exception_v2)

    wrap_wsgi_application(module, 'App.__call__',
            framework=framework)

    wrap_function_wrapper(module, 'App._handle_exception',
            wrap_handle_exception)


def instrument_falcon_routing_util(module):
    if hasattr(module, 'map_http_methods'):
        wrap_function_wrapper(module, 'map_http_methods',
                wrap_responder)
    elif hasattr(module, 'create_http_method_map'):
        wrap_function_wrapper(module, 'create_http_method_map',
                wrap_responder)
