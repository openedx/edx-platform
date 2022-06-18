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

"""
This module implements utilities for context propagation for tracing across threads.
"""

import logging

from newrelic.common.object_wrapper import function_wrapper
from newrelic.core.trace_cache import trace_cache

_logger = logging.getLogger(__name__)


class ContextOf(object):
    def __init__(self, trace=None, request=None, trace_cache_id=None, strict=True):
        self.trace = None
        self.trace_cache = trace_cache()
        self.thread_id = None
        self.restore = None
        self.should_restore = False

        def log_propagation_failure(s):
            if strict:
                _logger.error(
                    "Runtime instrumentation error. Request context propagation failed. %s Report this issue to New Relic support.",
                    s,
                )
            else:
                _logger.debug(
                    "Request context propagation failed. %s This may be an issue if there's an active transaction. Consult with New Relic support if further issues arise.",
                    s,
                )

        # Extract trace if possible, else leave as None for safety
        if trace is None and request is None and trace_cache_id is None:
            if strict:
                log_propagation_failure("No trace or request provided.")
        elif trace is not None:
            self.trace = trace
        elif trace_cache_id is not None:
            self.trace = self.trace_cache._cache.get(trace_cache_id, None)
            if self.trace is None:
                log_propagation_failure("No trace with id %d." % trace_cache_id)
        elif hasattr(request, "_nr_trace") and request._nr_trace is not None:
            # Unpack traces from objects patched with them
            self.trace = request._nr_trace
        else:
            log_propagation_failure("No context attached to request.")

    def __enter__(self):
        if self.trace:
            self.thread_id = self.trace_cache.current_thread_id()

            # Save previous cache contents
            self.restore = self.trace_cache._cache.get(self.thread_id, None)
            self.should_restore = True

            # Set context in trace cache
            self.trace_cache._cache[self.thread_id] = self.trace

        return self

    def __exit__(self, exc, value, tb):
        if self.should_restore:
            if self.restore is not None:
                # Restore previous contents
                self.trace_cache._cache[self.thread_id] = self.restore
            else:
                # Remove entry from cache
                self.trace_cache._cache.pop(self.thread_id)


def context_wrapper(func, trace=None, request=None, trace_cache_id=None, strict=True):
    @function_wrapper
    def _context_wrapper(wrapped, instance, args, kwargs):
        with ContextOf(trace=trace, request=request, trace_cache_id=trace_cache_id, strict=strict):
            return wrapped(*args, **kwargs)

    return _context_wrapper(func)


async def context_wrapper_async(awaitable, trace=None, request=None, trace_cache_id=None, strict=True):
    with ContextOf(trace=trace, request=request, trace_cache_id=trace_cache_id, strict=strict):
        return await awaitable


def current_thread_id():
    return trace_cache().current_thread_id()
