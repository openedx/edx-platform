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

import newrelic.api.memcache_trace

def instrument(module):

    if hasattr(module.Client, 'add'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.add', 'add')
    if hasattr(module.Client, 'append'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.append', 'replace')
    if hasattr(module.Client, 'decr'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.decr', 'decr')
    if hasattr(module.Client, 'delete'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.delete', 'delete')
    if hasattr(module.Client, 'delete_multi'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.delete_multi', 'delete')
    if hasattr(module.Client, 'get'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.get', 'get')
    if hasattr(module.Client, 'get_multi'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.get_multi', 'get')
    if hasattr(module.Client, 'incr'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.incr', 'incr')
    if hasattr(module.Client, 'incr_multi'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.incr_multi', 'incr')
    if hasattr(module.Client, 'prepend'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.prepend', 'replace')
    if hasattr(module.Client, 'replace'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.replace', 'replace')
    if hasattr(module.Client, 'set'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.set', 'set')
    if hasattr(module.Client, 'set_multi'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.set_multi', 'set')
