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

from newrelic.api.datastore_trace import datastore_trace
from newrelic.common.object_wrapper import wrap_function_wrapper, ObjectProxy

class _nr_umemcache_Client_proxy_(ObjectProxy):

    @datastore_trace('Memcached', None, 'set')
    def set(self, *args, **kwargs):
        return self.__wrapped__.set(*args, **kwargs)

    @datastore_trace('Memcached', None, 'get')
    def get(self, *args, **kwargs):
        return self.__wrapped__.get(*args, **kwargs)

    @datastore_trace('Memcached', None, 'gets')
    def gets(self, *args, **kwargs):
        return self.__wrapped__.gets(*args, **kwargs)

    @datastore_trace('Memcached', None, 'get_multi')
    def get_multi(self, *args, **kwargs):
        return self.__wrapped__.get_multi(*args, **kwargs)

    @datastore_trace('Memcached', None, 'gets_multi')
    def gets_multi(self, *args, **kwargs):
        return self.__wrapped__.gets_multi(*args, **kwargs)

    @datastore_trace('Memcached', None, 'add')
    def add(self, *args, **kwargs):
        return self.__wrapped__.add(*args, **kwargs)

    @datastore_trace('Memcached', None, 'replace')
    def replace(self, *args, **kwargs):
        return self.__wrapped__.replace(*args, **kwargs)

    @datastore_trace('Memcached', None, 'append')
    def append(self, *args, **kwargs):
        return self.__wrapped__.append(*args, **kwargs)

    @datastore_trace('Memcached', None, 'prepend')
    def prepend(self, *args, **kwargs):
        return self.__wrapped__.prepend(*args, **kwargs)

    @datastore_trace('Memcached', None, 'delete')
    def delete(self, *args, **kwargs):
        return self.__wrapped__.delete(*args, **kwargs)

    @datastore_trace('Memcached', None, 'cas')
    def cas(self, *args, **kwargs):
        return self.__wrapped__.cas(*args, **kwargs)

    @datastore_trace('Memcached', None, 'incr')
    def incr(self, *args, **kwargs):
        return self.__wrapped__.incr(*args, **kwargs)

    @datastore_trace('Memcached', None, 'decr')
    def decr(self, *args, **kwargs):
        return self.__wrapped__.decr(*args, **kwargs)

    @datastore_trace('Memcached', None, 'stats')
    def stats(self, *args, **kwargs):
        return self.__wrapped__.stats(*args, **kwargs)

def _nr_umemcache_Client_wrapper_(wrapped, instance, args, kwargs):
    return _nr_umemcache_Client_proxy_(wrapped(*args, **kwargs))

def instrument_umemcache(module):
    wrap_function_wrapper(module, 'Client', _nr_umemcache_Client_wrapper_)
