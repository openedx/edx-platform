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

import functools
import logging

from newrelic.api.time_trace import TimeTrace, current_trace
from newrelic.common.async_wrapper import async_wrapper
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.core.database_node import DatabaseNode
from newrelic.core.stack_trace import current_stack

_logger = logging.getLogger(__name__)


def register_database_client(
    dbapi2_module, database_product, quoting_style="single", explain_query=None, explain_stmts=[], instance_info=None
):

    _logger.debug(
        "Registering database client module %r where database "
        "is %r, quoting style is %r, explain query statement is %r and "
        "the SQL statements on which explain plans can be run are %r.",
        dbapi2_module,
        database_product,
        quoting_style,
        explain_query,
        explain_stmts,
    )

    dbapi2_module._nr_database_product = database_product
    dbapi2_module._nr_quoting_style = quoting_style
    dbapi2_module._nr_explain_query = explain_query
    dbapi2_module._nr_explain_stmts = explain_stmts
    dbapi2_module._nr_instance_info = instance_info
    dbapi2_module._nr_datastore_instance_feature_flag = False


def enable_datastore_instance_feature(dbapi2_module):
    dbapi2_module._nr_datastore_instance_feature_flag = True


class DatabaseTrace(TimeTrace):

    __async_explain_plan_logged = False

    def __init__(
        self,
        sql,
        dbapi2_module=None,
        connect_params=None,
        cursor_params=None,
        sql_parameters=None,
        execute_params=None,
        host=None,
        port_path_or_id=None,
        database_name=None,
        **kwargs
    ):
        parent = None
        if kwargs:
            if len(kwargs) > 1:
                raise TypeError("Invalid keyword arguments:", kwargs)
            parent = kwargs["parent"]
        super(DatabaseTrace, self).__init__(parent)

        self.sql = sql

        self.dbapi2_module = dbapi2_module

        self.connect_params = connect_params
        self.cursor_params = cursor_params
        self.sql_parameters = sql_parameters
        self.execute_params = execute_params
        self.host = host
        self.port_path_or_id = port_path_or_id
        self.database_name = database_name

    def __enter__(self):
        result = super(DatabaseTrace, self).__enter__()
        if result and self.transaction:
            self.sql = self.transaction._intern_string(self.sql)
        return result

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (
            self.__class__.__name__,
            id(self),
            dict(sql=self.sql, dbapi2_module=self.dbapi2_module),
        )

    @property
    def is_async_mode(self):
        # Check for `async=1` keyword argument in connect_params, which
        # indicates that psycopg2 driver is being used in async mode.

        # In python 3.7+ the arg will be 'async_' because 'async' is a keyword
        # However, note that psycopg2 v2.7+ allows either one as aliases, so
        # we have to check both.

        try:
            _, kwargs = self.connect_params
        except TypeError:
            return False
        else:
            return ("async" in kwargs and kwargs["async"]) or ("async_" in kwargs and kwargs["async_"])

    def _log_async_warning(self):
        # Only log the warning the first time.

        if not DatabaseTrace.__async_explain_plan_logged:
            DatabaseTrace.__async_explain_plan_logged = True
            _logger.warning(
                "Explain plans are not supported for queries made over database connections in asynchronous mode."
            )

    def finalize_data(self, transaction, exc=None, value=None, tb=None):
        self.stack_trace = None

        connect_params = None
        cursor_params = None
        sql_parameters = None
        execute_params = None
        host = None
        port_path_or_id = None
        database_name = None

        settings = transaction.settings

        if not settings:
            return

        tt = settings.transaction_tracer
        agent_limits = settings.agent_limits
        ds_tracer = settings.datastore_tracer

        # Check settings, so that we only call instance_info when needed.

        instance_enabled = ds_tracer.instance_reporting.enabled
        db_name_enabled = ds_tracer.database_name_reporting.enabled

        if instance_enabled or db_name_enabled:

            if (
                self.dbapi2_module
                and self.connect_params
                and self.dbapi2_module._nr_datastore_instance_feature_flag
                and self.dbapi2_module._nr_instance_info is not None
            ):

                instance_info = self.dbapi2_module._nr_instance_info(*self.connect_params)

                if instance_enabled:
                    host, port_path_or_id, _ = instance_info

                if db_name_enabled:
                    _, _, database_name = instance_info

            else:
                if instance_enabled:
                    host = self.host
                    port_path_or_id = self.port_path_or_id

                if db_name_enabled:
                    database_name = self.database_name

        if tt.enabled and settings.collect_traces and tt.record_sql != "off":
            if self.duration >= tt.stack_trace_threshold:
                if transaction._stack_trace_count < agent_limits.slow_sql_stack_trace:
                    self.stack_trace = [transaction._intern_string(x) for x in current_stack(skip=2)]
                    transaction._stack_trace_count += 1

            if self.is_async_mode and tt.explain_enabled:
                self._log_async_warning()
            else:
                # Only remember all the params for the calls if know
                # there is a chance we will need to do an explain
                # plan. We never allow an explain plan to be done if
                # an exception occurred in doing the query in case
                # doing the explain plan with the same inputs could
                # cause further problems.

                if (
                    exc is None
                    and not self.is_async_mode
                    and tt.explain_enabled
                    and self.duration >= tt.explain_threshold
                    and self.connect_params is not None
                ):
                    if transaction._explain_plan_count < agent_limits.sql_explain_plans:
                        connect_params = self.connect_params
                        cursor_params = self.cursor_params
                        sql_parameters = self.sql_parameters
                        execute_params = self.execute_params
                        transaction._explain_plan_count += 1

        self.sql_format = tt.record_sql

        self.connect_params = connect_params
        self.cursor_params = cursor_params
        self.sql_parameters = sql_parameters
        self.execute_params = execute_params
        self.host = host
        self.port_path_or_id = port_path_or_id
        self.database_name = database_name

    def terminal_node(self):
        return True

    def create_node(self):
        return DatabaseNode(
            dbapi2_module=self.dbapi2_module,
            sql=self.sql,
            children=self.children,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            exclusive=self.exclusive,
            stack_trace=self.stack_trace,
            sql_format=self.sql_format,
            connect_params=self.connect_params,
            cursor_params=self.cursor_params,
            sql_parameters=self.sql_parameters,
            execute_params=self.execute_params,
            host=self.host,
            port_path_or_id=self.port_path_or_id,
            database_name=self.database_name,
            guid=self.guid,
            agent_attributes=self.agent_attributes,
            user_attributes=self.user_attributes,
        )


def DatabaseTraceWrapper(wrapped, sql, dbapi2_module=None):
    def _nr_database_trace_wrapper_(wrapped, instance, args, kwargs):
        wrapper = async_wrapper(wrapped)
        if not wrapper:
            parent = current_trace()
            if not parent:
                return wrapped(*args, **kwargs)
        else:
            parent = None

        if callable(sql):
            if instance is not None:
                _sql = sql(instance, *args, **kwargs)
            else:
                _sql = sql(*args, **kwargs)
        else:
            _sql = sql

        trace = DatabaseTrace(_sql, dbapi2_module, parent=parent)

        if wrapper:  # pylint: disable=W0125,W0126
            return wrapper(wrapped, trace)(*args, **kwargs)

        with trace:
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, _nr_database_trace_wrapper_)


def database_trace(sql, dbapi2_module=None):
    return functools.partial(DatabaseTraceWrapper, sql=sql, dbapi2_module=dbapi2_module)


def wrap_database_trace(module, object_path, sql, dbapi2_module=None):
    wrap_object(module, object_path, DatabaseTraceWrapper, (sql, dbapi2_module))
