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

import types

import newrelic.api.transaction
import newrelic.api.object_wrapper
import newrelic.api.function_trace

class stream_wrapper(object):
    def __init__(self, stream, filepath):
        self.__stream = stream
        self.__filepath = filepath
    def render(self, *args, **kwargs):
        return newrelic.api.function_trace.FunctionTraceWrapper(
                self.__stream.render, self.__filepath,
                'Template/Render')(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(self.__stream, name)
    def __iter__(self):
        return iter(self.__stream)
    def __or__(self, function):
        return self.__stream.__or__(function)
    def __str__(self):
        return self.__stream.__str__()
    def __unicode__(self):
        return self.__stream.__unicode__()
    def __html__(self):
        return self.__stream.__html__()

class wrap_template(object):
    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None
        self.__instance = instance
        self.__wrapped = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self.__wrapped.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __call__(self, *args, **kwargs):
        current_transaction = newrelic.api.transaction.current_transaction()
        if current_transaction and self.__instance:
            return stream_wrapper(self.__wrapped(*args, **kwargs),
                                  self.__instance.filepath)
        else:
            return self.__wrapped(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.__wrapped, name)

def instrument(module):

    if module.__name__ == 'genshi.template.base':

        newrelic.api.object_wrapper.wrap_object(
                module, 'Template.generate', wrap_template)
