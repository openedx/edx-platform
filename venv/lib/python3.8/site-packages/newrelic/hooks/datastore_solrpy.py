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

from newrelic.api.datastore_trace import wrap_datastore_trace

_solrpy_client_methods = ('query', 'add', 'add_many', 'delete', 'delete_many',
'delete_query', 'commit', 'optimize', 'raw_query')

def instrument_solrpy(module):
    for name in _solrpy_client_methods:
        if hasattr(module.SolrConnection, name):
            wrap_datastore_trace(module.SolrConnection, name,
                    product='Solr', target=None, operation=name)
