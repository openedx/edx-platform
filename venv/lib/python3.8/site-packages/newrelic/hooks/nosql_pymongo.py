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

import newrelic.api.function_trace

_methods = ['save', 'insert', 'update', 'drop', 'remove', 'find_one',
            'find', 'count', 'create_index', 'ensure_index', 'drop_indexes',
            'drop_index', 'reindex', 'index_information', 'options',
            'group', 'rename', 'distinct', 'map_reduce', 'inline_map_reduce',
            'find_and_modify']

def instrument_pymongo_connection(module):

    # Must name function explicitly as pymongo overrides the
    # __getattr__() method in a way that breaks introspection.

    newrelic.api.function_trace.wrap_function_trace(
        module, 'Connection.__init__',
        name='%s:Connection.__init__' % module.__name__)

def instrument_pymongo_collection(module):

    # Must name function explicitly as pymongo overrides the
    # __getattr__() method in a way that breaks introspection.

    for method in _methods:
        if hasattr(module.Collection, method):
            #newrelic.api.function_trace.wrap_function_trace(
            #        module, 'Collection.%s' % method,
            #        name=method, group='Custom/MongoDB')
            newrelic.api.function_trace.wrap_function_trace(
                    module, 'Collection.%s' % method,
                    name='%s:Collection.%s' % (module.__name__, method))
