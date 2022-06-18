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

from newrelic.common.object_wrapper import wrap_object
from newrelic.api.database_trace import register_database_client

from newrelic.hooks.database_psycopg2 import instance_info


def instrument_postgresql_driver_dbapi20(module):
    register_database_client(module, database_product='Postgres',
            quoting_style='single+dollar', explain_query='explain',
            explain_stmts=('select', 'insert', 'update', 'delete'),
            instance_info=instance_info)

    from newrelic.hooks.database_psycopg2 import ConnectionFactory

    wrap_object(module, 'connect', ConnectionFactory, (module,))


def instrument_postgresql_interface_proboscis_dbapi2(module):
    register_database_client(module, database_product='Postgres',
            quoting_style='single+dollar', explain_query='explain',
            explain_stmts=('select', 'insert', 'update', 'delete'),
            instance_info=instance_info)

    from newrelic.hooks.database_dbapi2 import ConnectionFactory

    wrap_object(module, 'connect', ConnectionFactory, (module,))
