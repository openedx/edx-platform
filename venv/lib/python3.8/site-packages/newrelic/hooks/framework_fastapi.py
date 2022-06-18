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

from copy import copy

from newrelic.api.function_trace import FunctionTraceWrapper
from newrelic.api.time_trace import current_trace
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_function_wrapper


def wrap_run_endpoint_function(wrapped, instance, args, kwargs):
    trace = current_trace()
    if trace and trace.transaction:
        dependant = kwargs["dependant"]
        name = callable_name(dependant.call)
        trace.transaction.set_transaction_name(name)

        dependant = kwargs["dependant"] = copy(dependant)
        dependant.call = FunctionTraceWrapper(dependant.call)
        return wrapped(*args, **kwargs)

    return wrapped(*args, **kwargs)


def instrument_fastapi_routing(module):
    if hasattr(module, "run_endpoint_function"):
        wrap_function_wrapper(module, "run_endpoint_function", wrap_run_endpoint_function)
