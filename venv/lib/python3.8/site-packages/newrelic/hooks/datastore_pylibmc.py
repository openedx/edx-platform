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

_memcache_client_methods = ('get', 'gets', 'set', 'replace', 'add',
    'prepend', 'append', 'cas', 'delete', 'incr', 'decr', 'incr_multi',
    'get_multi', 'set_multi', 'add_multi', 'delete_multi', 'get_stats',
    'flush_all', 'touch')

def instrument_pylibmc_client(module):
    for name in _memcache_client_methods:
        if hasattr(module.Client, name):
            wrap_datastore_trace(module.Client, name,
                    product='Memcached', target=None, operation=name)
