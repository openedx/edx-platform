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

"""This module implements the communications layer with the data collector.

"""

from __future__ import print_function

import logging

from newrelic.common.agent_http import (
    ApplicationModeClient,
    DeveloperModeClient,
    ServerlessModeClient,
)
from newrelic.core.agent_protocol import AgentProtocol, ServerlessModeProtocol
from newrelic.core.agent_streaming import StreamingRpc
from newrelic.core.config import global_settings

_logger = logging.getLogger(__name__)


class Session(object):
    PROTOCOL = AgentProtocol
    CLIENT = ApplicationModeClient

    def __init__(self, app_name, linked_applications, environment, settings):
        self._protocol = self.PROTOCOL.connect(
            app_name, linked_applications, environment, settings, client_cls=self.CLIENT
        )
        self._rpc = None

    @property
    def configuration(self):
        return self._protocol.configuration

    @property
    def agent_run_id(self):
        return self._protocol.configuration.agent_run_id

    def close_connection(self):
        self._protocol.close_connection()

    def connect_span_stream(self, span_iterator, record_metric):
        if not self._rpc:
            host = self.configuration.infinite_tracing.trace_observer_host
            if not host:
                return

            port = self.configuration.infinite_tracing.trace_observer_port
            ssl = self.configuration.infinite_tracing.ssl
            endpoint = "{}:{}".format(host, port)

            if (
                self.configuration.distributed_tracing.enabled
                and self.configuration.span_events.enabled
                and self.configuration.collect_span_events
            ):

                metadata = (
                    ("agent_run_token", self.configuration.agent_run_id),
                    ("license_key", self.configuration.license_key),
                )

                rpc = self._rpc = StreamingRpc(
                    endpoint, span_iterator, metadata, record_metric, ssl=ssl
                )
                rpc.connect()
                return rpc

    def shutdown_span_stream(self):
        if self._rpc:
            self._rpc.close()

    def send_transaction_traces(self, transaction_traces):
        """Called to submit transaction traces. The transaction traces
        should be an iterable of individual traces.

        NOTE Although multiple traces could be supplied, the agent is
        currently only reporting on the slowest transaction in the most
        recent period being reported on.

        """

        if not transaction_traces:
            return

        payload = (self.agent_run_id, transaction_traces)
        return self._protocol.send("transaction_sample_data", payload)

    def send_transaction_events(self, sampling_info, sample_set):
        """Called to submit sample set for analytics."""

        payload = (self.agent_run_id, sampling_info, sample_set)
        return self._protocol.send("analytic_event_data", payload)

    def send_custom_events(self, sampling_info, custom_event_data):
        """Called to submit sample set for custom events."""

        payload = (self.agent_run_id, sampling_info, custom_event_data)
        return self._protocol.send("custom_event_data", payload)

    def send_span_events(self, sampling_info, span_event_data):
        """Called to submit sample set for span events."""

        payload = (self.agent_run_id, sampling_info, span_event_data)
        return self._protocol.send("span_event_data", payload)

    def send_metric_data(self, start_time, end_time, metric_data):
        """Called to submit metric data for specified period of time.
        Time values are seconds since UNIX epoch as returned by the
        time.time() function. The metric data should be iterable of
        specific metrics.
        """

        payload = (self.agent_run_id, start_time, end_time, metric_data)
        return self._protocol.send("metric_data", payload)

    def get_agent_commands(self):
        """Receive agent commands from the data collector.

        """

        payload = (self.agent_run_id,)
        return self._protocol.send("get_agent_commands", payload)

    def send_errors(self, errors):
        """Called to submit errors. The errors should be an iterable
        of individual error details.

        NOTE Although the details for each error carries a timestamp,
        the data collector appears to ignore it and overrides it with
        the timestamp that the data is received by the data collector.

        """
        payload = (self.agent_run_id, errors)
        return self._protocol.send("error_data", payload)

    def send_error_events(self, sampling_info, error_data):
        """Called to submit sample set for error events."""

        payload = (self.agent_run_id, sampling_info, error_data)
        return self._protocol.send("error_event_data", payload)

    def send_sql_traces(self, sql_traces):
        """Called to sub SQL traces. The SQL traces should be an
        iterable of individual SQL details.

        NOTE The agent currently only reports on the 10 slowest SQL
        queries in the most recent period being reported on.

        """

        payload = (sql_traces,)
        return self._protocol.send("sql_trace_data", payload)

    def send_agent_command_results(self, cmd_results):
        """Acknowledge the receipt of an agent command."""

        payload = (self.agent_run_id, cmd_results)

        return self._protocol.send("agent_command_results", payload)

    def send_profile_data(self, profile_data):
        """Called to submit Profile Data.
        """

        payload = (self.agent_run_id, profile_data)
        return self._protocol.send("profile_data", payload)

    def shutdown_session(self):
        """Called to perform orderly deregistration of agent run against
        the data collector, rather than simply dropping the connection and
        relying on data collector to surmise that agent run is finished
        due to no more data being reported.

        """

        payload = (self.agent_run_id,)
        return self._protocol.send("shutdown", payload)

    def finalize(self):
        return self._protocol.finalize()


class DeveloperModeSession(Session):
    CLIENT = DeveloperModeClient

    def connect_span_stream(self, span_iterator, record_metric):
        if self.configuration.debug.connect_span_stream_in_developer_mode:
            super(DeveloperModeSession, self).connect_span_stream(
                span_iterator, record_metric
            )


class ServerlessModeSession(Session):
    PROTOCOL = ServerlessModeProtocol
    CLIENT = ServerlessModeClient

    @staticmethod
    def connect_span_stream(*args, **kwargs):
        pass

    @staticmethod
    def get_agent_commands(*args, **kwargs):
        return ()

    @staticmethod
    def shutdown_session():
        pass


def create_session(license_key, app_name, linked_applications, environment):
    settings = global_settings()
    if settings.serverless_mode.enabled:
        return ServerlessModeSession(
            app_name, linked_applications, environment, settings
        )
    elif settings.developer_mode:
        return DeveloperModeSession(
            app_name, linked_applications, environment, settings
        )
    else:
        return Session(app_name, linked_applications, environment, settings)
