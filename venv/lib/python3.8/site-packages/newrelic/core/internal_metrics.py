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

import functools
import sys
import types
import time
import threading

_context = threading.local()

class InternalTrace(object):

    def __init__(self, name, metrics=None):
        self.name = name
        self.metrics = metrics
        self.start = 0.0

    def __enter__(self):
        if self.metrics is None:
            self.metrics = getattr(_context, 'current', None)
        self.start = time.time()
        return self

    def __exit__(self, exc, value, tb):
        duration = max(self.start, time.time()) - self.start
        if self.metrics is not None:
            self.metrics.record_custom_metric(self.name, duration)

class InternalTraceWrapper(object):

    def __init__(self, wrapped, name):
        if type(wrapped) == type(()):
            (instance, wrapped) = wrapped
        else:
            instance = None
        self.__instance = instance
        self.__wrapped = wrapped
        self.__name = name

    def __getattr__(self, name):
        return getattr(self.__wrapped, name)

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self.__wrapped.__get__(instance, klass)
        return self.__class__((instance, descriptor), self.__name)

    def __call__(self, *args, **kwargs):
        metrics = getattr(_context, 'current', None)

        if metrics is None:
            return self.__wrapped(*args, **kwargs)

        with InternalTrace(self.__name, metrics):
            return self.__wrapped(*args, **kwargs)

class InternalTraceContext(object):

    def __init__(self, metrics):
        self.previous = None
        self.metrics = metrics

    def __enter__(self):
        self.previous = getattr(_context, 'current', None)
        _context.current = self.metrics
        return self

    def __exit__(self, exc, value, tb):
        if self.previous is not None:
            _context.current = self.previous

def internal_trace(name=None):
    def decorator(wrapped):
        return InternalTraceWrapper(wrapped, name)
    return decorator

def wrap_internal_trace(module, object_path, name=None):
    newrelic.api.object_wrapper.wrap_object(module, object_path,
            InternalTraceWrapper, (name,))

def internal_metric(name, value):
    metrics = getattr(_context, 'current', None)
    if metrics is not None:
        metrics.record_custom_metric(name, value)

def internal_count_metric(name, count):
    """Create internal metric where only count has a value.

    All other fields have a value of 0.
    """

    count_metric = {'count': count}
    internal_metric(name, count_metric)
