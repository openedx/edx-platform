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
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_object

from newrelic.hooks.database_dbapi2 import (ConnectionWrapper as
        DBAPI2ConnectionWrapper, ConnectionFactory as DBAPI2ConnectionFactory)

class ConnectionWrapper(DBAPI2ConnectionWrapper):

    def __enter__(self):
        name = callable_name(self.__wrapped__.__enter__)
        with FunctionTrace(name):
            self.__wrapped__.__enter__()

        # Must return a reference to self as otherwise will be
        # returning the inner connection object. If 'as' is used
        # with the 'with' statement this will mean no longer
        # using the wrapped connection object and nothing will be
        # tracked.

        return self

    def __exit__(self, exc, value, tb):
        name = callable_name(self.__wrapped__.__exit__)
        with FunctionTrace(name):
            # XXX The pymssql client doesn't appear to to force a
            # commit or rollback from __exit__() explicitly. Need
            # to work out what its behaviour is around auto commit
            # and rollback.

            #if exc is None:
            #    with DatabaseTrace(transaction, 'COMMIT',
            #            self._nr_dbapi2_module):
            #        return self.__wrapped__.__exit__(exc, value, tb)
            #else:
            #    with DatabaseTrace(transaction, 'ROLLBACK',
            #            self._nr_dbapi2_module):
            #        return self.__wrapped__.__exit__(exc, value, tb)

            return self.__wrapped__.__exit__(exc, value, tb)

class ConnectionFactory(DBAPI2ConnectionFactory):

    __connection_wrapper__ = ConnectionWrapper

def instrument_pymssql(module):
    # XXX Don't believe MSSQL provides a simple means of doing an
    # explain plan using one SQL statement prefix, eg., 'EXPLAIN'.

    register_database_client(module, database_product='MSSQL',
            quoting_style='single')

    wrap_object(module, 'connect', ConnectionFactory, (module,))
