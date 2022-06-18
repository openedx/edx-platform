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

from newrelic.api.memcache_trace import memcache_trace
from newrelic.api.object_wrapper import ObjectWrapper

class Client(ObjectWrapper):

    def __init__(self, wrapped):
        super(Client, self).__init__(wrapped, None, None)

    @memcache_trace('set')
    def set(self, *args, **kwargs):
        return self._nr_next_object.set(*args, **kwargs)

    @memcache_trace('get')
    def get(self, *args, **kwargs):
        return self._nr_next_object.get(*args, **kwargs)

    @memcache_trace('get')
    def gets(self, *args, **kwargs):
        return self._nr_next_object.gets(*args, **kwargs)

    @memcache_trace('get')
    def get_multi(self, *args, **kwargs):
        return self._nr_next_object.get_multi(*args, **kwargs)

    @memcache_trace('get')
    def gets_multi(self, *args, **kwargs):
        return self._nr_next_object.gets_multi(*args, **kwargs)

    @memcache_trace('add')
    def add(self, *args, **kwargs):
        return self._nr_next_object.add(*args, **kwargs)

    @memcache_trace('replace')
    def replace(self, *args, **kwargs):
        return self._nr_next_object.replace(*args, **kwargs)

    @memcache_trace('replace')
    def append(self, *args, **kwargs):
        return self._nr_next_object.append(*args, **kwargs)

    @memcache_trace('replace')
    def prepend(self, *args, **kwargs):
        return self._nr_next_object.prepend(*args, **kwargs)

    @memcache_trace('delete')
    def delete(self, *args, **kwargs):
        return self._nr_next_object.delete(*args, **kwargs)

    @memcache_trace('replace')
    def cas(self, *args, **kwargs):
        return self._nr_next_object.cas(*args, **kwargs)

    @memcache_trace('incr')
    def incr(self, *args, **kwargs):
        return self._nr_next_object.incr(*args, **kwargs)

    @memcache_trace('decr')
    def decr(self, *args, **kwargs):
        return self._nr_next_object.decr(*args, **kwargs)

def instrument(module):

    _Client = module.Client

    def _client(*args, **kwargs):
        return Client(_Client(*args, **kwargs))

    module.Client = _client
