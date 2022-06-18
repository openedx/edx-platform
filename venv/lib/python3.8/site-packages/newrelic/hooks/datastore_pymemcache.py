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

_memcache_client_methods = ('set', 'set_many', 'add', 'replace', 'append',
    'prepend', 'cas', 'get', 'get_many', 'gets', 'gets_many', 'delete',
    'delete_many', 'incr', 'decr', 'touch', 'stats', 'flush_all', 'quit')

def instrument_pymemcache_client(module):
    for name in _memcache_client_methods:
        if hasattr(module.Client, name):
            wrap_datastore_trace(module.Client, name,
                    product='Memcached', target=None, operation=name)
