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

import os

from newrelic.api.database_trace import (enable_datastore_instance_feature,
        DatabaseTrace, register_database_client)
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_object

from newrelic.hooks.database_dbapi2 import (ConnectionWrapper as
        DBAPI2ConnectionWrapper, ConnectionFactory as DBAPI2ConnectionFactory)

class ConnectionWrapper(DBAPI2ConnectionWrapper):

    def __enter__(self):
        transaction = current_transaction()
        name = callable_name(self.__wrapped__.__enter__)
        with FunctionTrace(name):
            cursor = self.__wrapped__.__enter__()

        # The __enter__() method of original connection object returns
        # a new cursor instance for use with 'as' assignment. We need
        # to wrap that in a cursor wrapper otherwise we will not track
        # any queries done via it.

        return self.__cursor_wrapper__(cursor, self._nr_dbapi2_module,
                self._nr_connect_params, None)

    def __exit__(self, exc, value, tb):
        transaction = current_transaction()
        name = callable_name(self.__wrapped__.__exit__)
        with FunctionTrace(name):
            if exc is None:
                with DatabaseTrace('COMMIT',
                        self._nr_dbapi2_module, self._nr_connect_params):
                    return self.__wrapped__.__exit__(exc, value, tb)
            else:
                with DatabaseTrace('ROLLBACK',
                        self._nr_dbapi2_module, self._nr_connect_params):
                    return self.__wrapped__.__exit__(exc, value, tb)

class ConnectionFactory(DBAPI2ConnectionFactory):

    __connection_wrapper__ = ConnectionWrapper

def instance_info(args, kwargs):
    def _bind_params(host=None, user=None, passwd=None, db=None, port=None,
            unix_socket=None, conv=None, connect_timeout=None, compress=None,
            named_pipe=None, init_command=None, read_default_file=None,
            read_default_group=None, *args, **kwargs):
        return (host, port, db, unix_socket,
                read_default_file, read_default_group)

    params = _bind_params(*args, **kwargs)
    host, port, db, unix_socket, read_default_file, read_default_group = params
    explicit_host = host

    port_path_or_id = None
    if read_default_file or read_default_group:
        host = host or 'default'
        port_path_or_id = 'unknown'
    elif not host:
        host = 'localhost'

    if host == 'localhost':
        # precedence: explicit -> cnf (if used) -> env -> 'default'
        port_path_or_id = (unix_socket or
                port_path_or_id or
                os.getenv('MYSQL_UNIX_PORT', 'default'))
    elif explicit_host:
        # only reach here if host is explicitly passed in
        port = port and str(port)
        # precedence: explicit -> cnf (if used) -> env -> '3306'
        port_path_or_id = (port or
                port_path_or_id or
                os.getenv('MYSQL_TCP_PORT', '3306'))

    # There is no default database if omitted from the connect params
    # In this case, we should report unknown
    db = db or 'unknown'

    return (host, port_path_or_id, db)

def instrument_mysqldb(module):
    register_database_client(module, database_product='MySQL',
            quoting_style='single+double', explain_query='explain',
            explain_stmts=('select',), instance_info=instance_info)

    enable_datastore_instance_feature(module)

    wrap_object(module, 'connect', ConnectionFactory, (module,))

    # The connect() function is actually aliased with Connect() and
    # Connection, the later actually being the Connection type object.
    # Instrument Connect(), but don't instrument Connection in case that
    # interferes with direct type usage. If people are using the
    # Connection object directly, they should really be using connect().

    if hasattr(module, 'Connect'):
        wrap_object(module, 'Connect', ConnectionFactory, (module,))
