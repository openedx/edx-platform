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
from newrelic.common.object_wrapper import wrap_object

from newrelic.hooks.database_dbapi2 import ConnectionFactory

def instance_info(args, kwargs):
    host = kwargs.get('host')
    port = kwargs.get('port')
    db = kwargs.get('db')

    return (host, port, db)

def instrument_mysql_connector(module):
    register_database_client(module, database_product='MySQL',
            quoting_style='single+double', explain_query='explain',
            explain_stmts=('select',), instance_info=instance_info)

    wrap_object(module, 'connect', ConnectionFactory, (module,))

    # The connect() function is actually aliased with Connect() and
    # Connection, the later actually being the Connection type object.
    # Instrument Connect(), but don't instrument Connection in case that
    # interferes with direct type usage. If people are using the
    # Connection object directly, they should really be using connect().

    if hasattr(module, 'Connect'):
        wrap_object(module, 'Connect', ConnectionFactory, (module,))
