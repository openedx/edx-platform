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

from newrelic.api.database_trace import register_database_client
from newrelic.common.object_wrapper import wrap_object, ObjectProxy

from newrelic.hooks.database_dbapi2 import ConnectionFactory


class SessionPoolProxy(ObjectProxy):
    def __init__(self, pool, dbapi2_module):
        super(SessionPoolProxy, self).__init__(pool)
        self._nr_dbapi2_module = dbapi2_module

    def acquire(self, *args, **kwargs):
        return ConnectionFactory(
                self.__wrapped__.acquire,
                self._nr_dbapi2_module)(*args, **kwargs)

    def drop(self, connection, *args, **kwargs):
        if isinstance(connection, ObjectProxy):
            connection = connection.__wrapped__

        return self.__wrapped__.drop(connection, *args, **kwargs)

    def release(self, connection, *args, **kwargs):
        if isinstance(connection, ObjectProxy):
            connection = connection.__wrapped__

        return self.__wrapped__.release(connection, *args, **kwargs)


class CreateSessionPoolProxy(ObjectProxy):

    def __init__(self, pool_init, dbapi2_module):
        super(CreateSessionPoolProxy, self).__init__(pool_init)
        self._nr_dbapi2_module = dbapi2_module

    def __call__(self, *args, **kwargs):
        pool = self.__wrapped__(*args, **kwargs)
        return SessionPoolProxy(pool, self._nr_dbapi2_module)


def instrument_cx_oracle(module):
    register_database_client(module, database_product='Oracle',
            quoting_style='single+oracle')

    wrap_object(module, 'connect', ConnectionFactory, (module,))
    wrap_object(module, 'SessionPool', CreateSessionPoolProxy, (module,))
