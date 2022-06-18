# Copyright 2020-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Example event logger classes.

.. versionadded:: 3.11

These loggers can be registered using :func:`register` or
:class:`~pymongo.mongo_client.MongoClient`.

``monitoring.register(CommandLogger())``

or

``MongoClient(event_listeners=[CommandLogger()])``
"""


import logging

from pymongo import monitoring


class CommandLogger(monitoring.CommandListener):
    """A simple listener that logs command events.

    Listens for :class:`~pymongo.monitoring.CommandStartedEvent`,
    :class:`~pymongo.monitoring.CommandSucceededEvent` and
    :class:`~pymongo.monitoring.CommandFailedEvent` events and
    logs them at the `INFO` severity level using :mod:`logging`.
    .. versionadded:: 3.11
    """
    def started(self, event):
        logging.info("Command {0.command_name} with request id "
                     "{0.request_id} started on server "
                     "{0.connection_id}".format(event))

    def succeeded(self, event):
        logging.info("Command {0.command_name} with request id "
                     "{0.request_id} on server {0.connection_id} "
                     "succeeded in {0.duration_micros} "
                     "microseconds".format(event))

    def failed(self, event):
        logging.info("Command {0.command_name} with request id "
                     "{0.request_id} on server {0.connection_id} "
                     "failed in {0.duration_micros} "
                     "microseconds".format(event))


class ServerLogger(monitoring.ServerListener):
    """A simple listener that logs server discovery events.

    Listens for :class:`~pymongo.monitoring.ServerOpeningEvent`,
    :class:`~pymongo.monitoring.ServerDescriptionChangedEvent`,
    and :class:`~pymongo.monitoring.ServerClosedEvent`
    events and logs them at the `INFO` severity level using :mod:`logging`.

    .. versionadded:: 3.11
    """
    def opened(self, event):
        logging.info("Server {0.server_address} added to topology "
                     "{0.topology_id}".format(event))

    def description_changed(self, event):
        previous_server_type = event.previous_description.server_type
        new_server_type = event.new_description.server_type
        if new_server_type != previous_server_type:
            # server_type_name was added in PyMongo 3.4
            logging.info(
                "Server {0.server_address} changed type from "
                "{0.previous_description.server_type_name} to "
                "{0.new_description.server_type_name}".format(event))

    def closed(self, event):
        logging.warning("Server {0.server_address} removed from topology "
                        "{0.topology_id}".format(event))


class HeartbeatLogger(monitoring.ServerHeartbeatListener):
    """A simple listener that logs server heartbeat events.

    Listens for :class:`~pymongo.monitoring.ServerHeartbeatStartedEvent`,
    :class:`~pymongo.monitoring.ServerHeartbeatSucceededEvent`,
    and :class:`~pymongo.monitoring.ServerHeartbeatFailedEvent`
    events and logs them at the `INFO` severity level using :mod:`logging`.

    .. versionadded:: 3.11
    """
    def started(self, event):
        logging.info("Heartbeat sent to server "
                     "{0.connection_id}".format(event))

    def succeeded(self, event):
        # The reply.document attribute was added in PyMongo 3.4.
        logging.info("Heartbeat to server {0.connection_id} "
                     "succeeded with reply "
                     "{0.reply.document}".format(event))

    def failed(self, event):
        logging.warning("Heartbeat to server {0.connection_id} "
                        "failed with error {0.reply}".format(event))


class TopologyLogger(monitoring.TopologyListener):
    """A simple listener that logs server topology events.

    Listens for :class:`~pymongo.monitoring.TopologyOpenedEvent`,
    :class:`~pymongo.monitoring.TopologyDescriptionChangedEvent`,
    and :class:`~pymongo.monitoring.TopologyClosedEvent`
    events and logs them at the `INFO` severity level using :mod:`logging`.

    .. versionadded:: 3.11
    """
    def opened(self, event):
        logging.info("Topology with id {0.topology_id} "
                     "opened".format(event))

    def description_changed(self, event):
        logging.info("Topology description updated for "
                     "topology id {0.topology_id}".format(event))
        previous_topology_type = event.previous_description.topology_type
        new_topology_type = event.new_description.topology_type
        if new_topology_type != previous_topology_type:
            # topology_type_name was added in PyMongo 3.4
            logging.info(
                "Topology {0.topology_id} changed type from "
                "{0.previous_description.topology_type_name} to "
                "{0.new_description.topology_type_name}".format(event))
        # The has_writable_server and has_readable_server methods
        # were added in PyMongo 3.4.
        if not event.new_description.has_writable_server():
            logging.warning("No writable servers available.")
        if not event.new_description.has_readable_server():
            logging.warning("No readable servers available.")

    def closed(self, event):
        logging.info("Topology with id {0.topology_id} "
                     "closed".format(event))


class ConnectionPoolLogger(monitoring.ConnectionPoolListener):
    """A simple listener that logs server connection pool events.

    Listens for :class:`~pymongo.monitoring.PoolCreatedEvent`,
    :class:`~pymongo.monitoring.PoolClearedEvent`,
    :class:`~pymongo.monitoring.PoolClosedEvent`,
    :~pymongo.monitoring.class:`ConnectionCreatedEvent`,
    :class:`~pymongo.monitoring.ConnectionReadyEvent`,
    :class:`~pymongo.monitoring.ConnectionClosedEvent`,
    :class:`~pymongo.monitoring.ConnectionCheckOutStartedEvent`,
    :class:`~pymongo.monitoring.ConnectionCheckOutFailedEvent`,
    :class:`~pymongo.monitoring.ConnectionCheckedOutEvent`,
    and :class:`~pymongo.monitoring.ConnectionCheckedInEvent`
    events and logs them at the `INFO` severity level using :mod:`logging`.

    .. versionadded:: 3.11
    """
    def pool_created(self, event):
        logging.info("[pool {0.address}] pool created".format(event))

    def pool_cleared(self, event):
        logging.info("[pool {0.address}] pool cleared".format(event))

    def pool_closed(self, event):
        logging.info("[pool {0.address}] pool closed".format(event))

    def connection_created(self, event):
        logging.info("[pool {0.address}][conn #{0.connection_id}] "
                     "connection created".format(event))

    def connection_ready(self, event):
        logging.info("[pool {0.address}][conn #{0.connection_id}] "
                     "connection setup succeeded".format(event))

    def connection_closed(self, event):
        logging.info("[pool {0.address}][conn #{0.connection_id}] "
                     "connection closed, reason: "
                     "{0.reason}".format(event))

    def connection_check_out_started(self, event):
        logging.info("[pool {0.address}] connection check out "
                     "started".format(event))

    def connection_check_out_failed(self, event):
        logging.info("[pool {0.address}] connection check out "
                     "failed, reason: {0.reason}".format(event))

    def connection_checked_out(self, event):
        logging.info("[pool {0.address}][conn #{0.connection_id}] "
                     "connection checked out of pool".format(event))

    def connection_checked_in(self, event):
        logging.info("[pool {0.address}][conn #{0.connection_id}] "
                     "connection checked into pool".format(event))
