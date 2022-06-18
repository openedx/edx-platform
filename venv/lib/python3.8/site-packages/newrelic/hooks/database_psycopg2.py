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

import inspect
import os

from newrelic.api.database_trace import (enable_datastore_instance_feature,
        register_database_client, DatabaseTrace)
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (wrap_object, ObjectProxy,
        wrap_function_wrapper)

from newrelic.hooks.database_dbapi2 import (ConnectionWrapper as
        DBAPI2ConnectionWrapper, ConnectionFactory as DBAPI2ConnectionFactory,
        CursorWrapper as DBAPI2CursorWrapper, DEFAULT)

try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote
try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

from newrelic.packages.urllib3 import util as ul3_util


# These functions return True if a non-default connection or cursor class is
# used. If the default connection and cursor are used without any unknown
# arguments, we can safely drop all cursor parameters to generate explain
# plans. Explain plans do not work with named cursors.
def _bind_connect(
        dsn=None, connection_factory=None, cursor_factory=None,
        *args, **kwargs):
    return bool(connection_factory or cursor_factory)


def _bind_cursor(
        name=None, cursor_factory=None, scrollable=None,
        withhold=False, *args, **kwargs):
    return bool(cursor_factory or args or kwargs)


class CursorWrapper(DBAPI2CursorWrapper):

    def execute(self, sql, parameters=DEFAULT, *args, **kwargs):
        if hasattr(sql, 'as_string'):
            sql = sql.as_string(self)

        return super(CursorWrapper, self).execute(sql, parameters, *args,
                **kwargs)

    def __enter__(self):
        self.__wrapped__.__enter__()
        return self

    def executemany(self, sql, seq_of_parameters):
        if hasattr(sql, 'as_string'):
            sql = sql.as_string(self)

        return super(CursorWrapper, self).executemany(sql, seq_of_parameters)


class ConnectionSaveParamsWrapper(DBAPI2ConnectionWrapper):

    __cursor_wrapper__ = CursorWrapper

    def __enter__(self):
        transaction = current_transaction()
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


# This connection wrapper does not save cursor parameters for explain plans. It
# is only used for the default connection class.
class ConnectionWrapper(ConnectionSaveParamsWrapper):

    def cursor(self, *args, **kwargs):
        # If any unknown cursor params are detected or a cursor factory is
        # used, store params for explain plans later.
        if _bind_cursor(*args, **kwargs):
            cursor_params = (args, kwargs)
        else:
            cursor_params = None

        return self.__cursor_wrapper__(self.__wrapped__.cursor(
                *args, **kwargs), self._nr_dbapi2_module,
                self._nr_connect_params, cursor_params)


class ConnectionFactory(DBAPI2ConnectionFactory):

    __connection_wrapper__ = ConnectionWrapper

    def __call__(self, *args, **kwargs):
        if _bind_connect(*args, **kwargs):
            self.__connection_wrapper__ = ConnectionSaveParamsWrapper

        return super(ConnectionFactory, self).__call__(*args, **kwargs)


def instance_info(args, kwargs):

    p_host, p_hostaddr, p_port, p_dbname = _parse_connect_params(args, kwargs)
    host, port, db_name = _add_defaults(p_host, p_hostaddr, p_port, p_dbname)

    return (host, port, db_name)


def _parse_connect_params(args, kwargs):

    def _bind_params(dsn=None, *args, **kwargs):
        return dsn

    dsn = _bind_params(*args, **kwargs)

    try:
        if dsn and (dsn.startswith('postgres://') or
                dsn.startswith('postgresql://')):

            # Parse dsn as URI
            #
            # According to PGSQL, connect URIs are in the format of RFC 3896
            # https://www.postgresql.org/docs/9.5/static/libpq-connect.html

            parsed_uri = ul3_util.parse_url(dsn)

            host = parsed_uri.hostname or None
            host = host and unquote(host)

            # ipv6 brackets [] are contained in the URI hostname
            # and should be removed
            host = host and host.strip('[]')

            port = parsed_uri.port

            db_name = parsed_uri.path
            db_name = db_name and db_name.lstrip('/')
            db_name = db_name or None

            query = parsed_uri.query or ''
            qp = dict(parse_qsl(query))

            # Query parameters override hierarchical values in URI.

            host = qp.get('host') or host or None
            hostaddr = qp.get('hostaddr')
            port = qp.get('port') or port
            db_name = qp.get('dbname') or db_name

        elif dsn:

            # Parse dsn as a key-value connection string

            kv = dict([pair.split('=', 2) for pair in dsn.split()])
            host = kv.get('host')
            hostaddr = kv.get('hostaddr')
            port = kv.get('port')
            db_name = kv.get('dbname')

        else:

            # No dsn, so get the instance info from keyword arguments.

            host = kwargs.get('host')
            hostaddr = kwargs.get('hostaddr')
            port = kwargs.get('port')
            db_name = kwargs.get('database')

        # Ensure non-None values are strings.

        (host, hostaddr, port, db_name) = [str(s) if s is not None else s
                for s in (host, hostaddr, port, db_name)]

    except Exception:
        host = 'unknown'
        hostaddr = 'unknown'
        port = 'unknown'
        db_name = 'unknown'

    return (host, hostaddr, port, db_name)


def _add_defaults(parsed_host, parsed_hostaddr, parsed_port, parsed_database):

    # ENV variables set the default values

    parsed_host = parsed_host or os.environ.get('PGHOST')
    parsed_hostaddr = parsed_hostaddr or os.environ.get('PGHOSTADDR')
    parsed_port = parsed_port or os.environ.get('PGPORT')
    database = parsed_database or os.environ.get('PGDATABASE') or 'default'

    # If hostaddr is present, we use that, since host is used for auth only.

    parsed_host = parsed_hostaddr or parsed_host

    if parsed_host is None:
        host = 'localhost'
        port = 'default'
    elif parsed_host.startswith('/'):
        host = 'localhost'
        port = '%s/.s.PGSQL.%s' % (parsed_host, parsed_port or '5432')
    else:
        host = parsed_host
        port = parsed_port or '5432'

    return (host, port, database)


def instrument_psycopg2(module):
    register_database_client(module, database_product='Postgres',
            quoting_style='single+dollar', explain_query='explain',
            explain_stmts=('select', 'insert', 'update', 'delete'),
            instance_info=instance_info)

    enable_datastore_instance_feature(module)

    wrap_object(module, 'connect', ConnectionFactory, (module,))


def wrapper_psycopg2_register_type(wrapped, instance, args, kwargs):
    def _bind_params(obj, scope=None):
        return obj, scope

    obj, scope = _bind_params(*args, **kwargs)

    if isinstance(scope, ObjectProxy):
        scope = scope.__wrapped__

    if scope is not None:
        return wrapped(obj, scope)
    else:
        return wrapped(obj)


def wrapper_psycopg2_as_string(wrapped, instance, args, kwargs):
    def _bind_params(context, *args, **kwargs):
        return context, args, kwargs

    context, _args, _kwargs = _bind_params(*args, **kwargs)

    # Unwrap the context for string conversion since psycopg2 uses duck typing
    # and a TypeError will be raised if a wrapper is used.
    if hasattr(context, '__wrapped__'):
        context = context.__wrapped__

    return wrapped(context, *_args, **_kwargs)


# As we can't get in reliably and monkey patch the register_type()
# function in psycopg2._psycopg2 before it is imported, we also need to
# monkey patch the other references to it in other psycopg2 sub modules.
# In doing that we need to make sure it has not already been monkey
# patched by checking to see if it is already an ObjectProxy.
def instrument_psycopg2__psycopg2(module):
    if hasattr(module, 'register_type'):
        if not isinstance(module.register_type, ObjectProxy):
            wrap_function_wrapper(module, 'register_type',
                    wrapper_psycopg2_register_type)


def instrument_psycopg2_extensions(module):
    if hasattr(module, 'register_type'):
        if not isinstance(module.register_type, ObjectProxy):
            wrap_function_wrapper(module, 'register_type',
                    wrapper_psycopg2_register_type)


def instrument_psycopg2__json(module):
    if hasattr(module, 'register_type'):
        if not isinstance(module.register_type, ObjectProxy):
            wrap_function_wrapper(module, 'register_type',
                    wrapper_psycopg2_register_type)


def instrument_psycopg2__range(module):
    if hasattr(module, 'register_type'):
        if not isinstance(module.register_type, ObjectProxy):
            wrap_function_wrapper(module, 'register_type',
                    wrapper_psycopg2_register_type)


def instrument_psycopg2_sql(module):
    if (hasattr(module, 'Composable') and
            hasattr(module.Composable, 'as_string')):
        for name, cls in inspect.getmembers(module):
            if not inspect.isclass(cls):
                continue

            if not issubclass(cls, module.Composable):
                continue

            wrap_function_wrapper(module, name + '.as_string',
                    wrapper_psycopg2_as_string)
