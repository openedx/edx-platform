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

import newrelic.packages.six as six

import newrelic.api.transaction
import newrelic.api.function_trace
import newrelic.api.object_wrapper
import newrelic.api.in_function


class MethodWrapper(object):

    def __init__(self, wrapped, priority=None):
        self._nr_name = newrelic.api.object_wrapper.callable_name(wrapped)
        self._nr_wrapped = wrapped
        self._nr_priority = priority

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_wrapped.__get__(instance, klass)
        return self.__class__(descriptor)

    def __getattr__(self, name):
        return getattr(self._nr_wrapped, name)

    def __call__(self, *args, **kwargs):
        transaction = newrelic.api.transaction.current_transaction()
        if transaction:
            transaction.set_transaction_name(self._nr_name,
                    priority=self._nr_priority)
            with newrelic.api.function_trace.FunctionTrace(
                    name=self._nr_name):
                return self._nr_wrapped(*args, **kwargs)
        else:
            return self._nr_wrapped(*args, **kwargs)


class ResourceInitWrapper(object):

    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None
        self.__instance = instance
        self._nr_wrapped = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_wrapped.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __getattr__(self, name):
        return getattr(self._nr_wrapped, name)

    def __call__(self, *args, **kwargs):
        self._nr_wrapped(*args, **kwargs)
        handler = self.__instance.handler
        for name in six.itervalues(self.__instance.callmap):
            if hasattr(handler, name):
                setattr(handler, name, MethodWrapper(
                        getattr(handler, name), priority=6))


def instrument_piston_resource(module):

    newrelic.api.object_wrapper.wrap_object(module,
            'Resource.__init__', ResourceInitWrapper)


def instrument_piston_doc(module):

    def in_HandlerMethod_init(self, method, *args, **kwargs):
        if isinstance(method, MethodWrapper):
            method = method._nr_wrapped
        return ((self, method) + args, kwargs)

    newrelic.api.in_function.wrap_in_function(module,
            'HandlerMethod.__init__', in_HandlerMethod_init)
