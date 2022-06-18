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

from newrelic.api.database_trace import DatabaseTrace, register_database_client
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_object, ObjectProxy
from newrelic.core.config import global_settings

DEFAULT = object()

class CursorWrapper(ObjectProxy):

    def __init__(self, cursor, dbapi2_module, connect_params, cursor_params):
        super(CursorWrapper, self).__init__(cursor)
        self._nr_dbapi2_module = dbapi2_module
        self._nr_connect_params = connect_params
        self._nr_cursor_params = cursor_params

    def execute(self, sql, parameters=DEFAULT, *args, **kwargs):
        if parameters is not DEFAULT:
            with DatabaseTrace(sql, self._nr_dbapi2_module,
                    self._nr_connect_params, self._nr_cursor_params,
                    parameters, (args, kwargs)):
                return self.__wrapped__.execute(sql, parameters,
                        *args, **kwargs)
        else:
            with DatabaseTrace(sql, self._nr_dbapi2_module,
                    self._nr_connect_params, self._nr_cursor_params,
                    None, (args, kwargs)):
                return self.__wrapped__.execute(sql, **kwargs)

    def executemany(self, sql, seq_of_parameters):
        try:
            seq_of_parameters = list(seq_of_parameters)
            parameters = seq_of_parameters[0]
        except (TypeError, IndexError):
            parameters = DEFAULT
        if parameters is not DEFAULT:
            with DatabaseTrace(sql, self._nr_dbapi2_module,
                    self._nr_connect_params, self._nr_cursor_params,
                    parameters):
                return self.__wrapped__.executemany(sql, seq_of_parameters)
        else:
            with DatabaseTrace(sql, self._nr_dbapi2_module,
                    self._nr_connect_params, self._nr_cursor_params):
                return self.__wrapped__.executemany(sql, seq_of_parameters)

    def callproc(self, procname, parameters=DEFAULT):
        with DatabaseTrace('CALL %s' % procname,
                self._nr_dbapi2_module, self._nr_connect_params):
            if parameters is not DEFAULT:
                return self.__wrapped__.callproc(procname, parameters)
            else:
                return self.__wrapped__.callproc(procname)

class ConnectionWrapper(ObjectProxy):

    __cursor_wrapper__ = CursorWrapper

    def __init__(self, connection, dbapi2_module, connect_params):
        super(ConnectionWrapper, self).__init__(connection)
        self._nr_dbapi2_module = dbapi2_module
        self._nr_connect_params = connect_params

    def cursor(self, *args, **kwargs):
        return self.__cursor_wrapper__(self.__wrapped__.cursor(
                *args, **kwargs), self._nr_dbapi2_module,
                self._nr_connect_params, (args, kwargs))

    def commit(self):
        with DatabaseTrace('COMMIT', self._nr_dbapi2_module,
                self._nr_connect_params):
            return self.__wrapped__.commit()

    def rollback(self):
        with DatabaseTrace('ROLLBACK', self._nr_dbapi2_module,
                self._nr_connect_params):
            return self.__wrapped__.rollback()

class ConnectionFactory(ObjectProxy):

    __connection_wrapper__ = ConnectionWrapper

    def __init__(self, connect, dbapi2_module):
        super(ConnectionFactory, self).__init__(connect)
        self._nr_dbapi2_module = dbapi2_module

    def __call__(self, *args, **kwargs):
        rollup = []
        rollup.append('Datastore/all')
        rollup.append('Datastore/%s/all' %
                self._nr_dbapi2_module._nr_database_product)

        with FunctionTrace(callable_name(self.__wrapped__),
                terminal=True, rollup=rollup):
            return self.__connection_wrapper__(self.__wrapped__(
                    *args, **kwargs), self._nr_dbapi2_module, (args, kwargs))

def instrument(module):
    register_database_client(module, 'DBAPI2', 'single')

    wrap_object(module, 'connect', ConnectionFactory, (module,))
