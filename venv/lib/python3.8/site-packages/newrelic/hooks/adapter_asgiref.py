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

from newrelic.api.time_trace import current_trace
from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.core.context import ContextOf, context_wrapper_async


def _bind_thread_handler(loop, source_task, *args, **kwargs):
    return source_task


def thread_handler_wrapper(wrapped, instance, args, kwargs):
    task = _bind_thread_handler(*args, **kwargs)
    with ContextOf(trace_cache_id=id(task), strict=False):
        return wrapped(*args, **kwargs)


def main_wrap_wrapper(wrapped, instance, args, kwargs):
    awaitable = wrapped(*args, **kwargs)
    return context_wrapper_async(awaitable, current_trace(), strict=False)


def instrument_asgiref_sync(module):
    wrap_function_wrapper(module, "SyncToAsync.thread_handler", thread_handler_wrapper)
    wrap_function_wrapper(module, "AsyncToSync.main_wrap", main_wrap_wrapper)
