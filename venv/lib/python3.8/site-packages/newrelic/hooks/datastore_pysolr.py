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

_pysolr_client_methods = ('search', 'more_like_this', 'suggest_terms', 'add',
'delete', 'commit', 'optimize', 'extract')

_pysolr_admin_methods = ('status', 'create', 'reload', 'rename', 'swap',
    'unload', 'load')

def instrument_pysolr(module):
    for name in _pysolr_client_methods:
        if hasattr(module.Solr, name):
            wrap_datastore_trace(module.Solr, name,
                    product='Solr', target=None, operation=name)

    if hasattr(module, 'SolrCoreAdmin'):
        for name in _pysolr_admin_methods:
            if hasattr(module.SolrCoreAdmin, name):
                wrap_datastore_trace(module.SolrCoreAdmin, name,
                        product='Solr', target=None,
                        operation='admin.%s' % name)
