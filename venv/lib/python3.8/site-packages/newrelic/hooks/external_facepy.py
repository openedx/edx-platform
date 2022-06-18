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

import newrelic.api.external_trace

def instrument(module):

    def url_query(graph_obj, method, path, *args, **kwargs):
        return '/'.join([graph_obj.url, path])

    newrelic.api.external_trace.wrap_external_trace(
            module, 'GraphAPI._query', 'facepy', url_query)

    #def url_method(graph_obj, path, *args, **kwargs):
        #return '/'.join([graph_obj.url, path])

    #newrelic.api.external_trace.wrap_external_trace(
            #module, 'GraphAPI.get', 'facepy', url_method)

    #newrelic.api.external_trace.wrap_external_trace(
            #module, 'GraphAPI.post', 'facepy', url_method)

    #newrelic.api.external_trace.wrap_external_trace(
            #module, 'GraphAPI.delete', 'facepy', url_method)

    #def url_search(graph_obj, path, *args, **kwargs):
        #return '/'.join([graph_obj.url, 'search'])

    #newrelic.api.external_trace.wrap_external_trace(
            #module, 'GraphAPI.search', 'facepy', url_search)
