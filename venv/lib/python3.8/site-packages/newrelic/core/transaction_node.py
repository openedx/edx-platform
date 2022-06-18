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

"""This module provides the transaction node type used as root in the
construction of the raw transaction trace hierarchy from which metrics are
then to be generated.

"""

from collections import namedtuple

import newrelic.core.error_collector
import newrelic.core.trace_node

from newrelic.core.metric import ApdexMetric, TimeMetric
from newrelic.core.string_table import StringTable
from newrelic.core.attribute import create_user_attributes
from newrelic.core.attribute_filter import (DST_ERROR_COLLECTOR,
        DST_TRANSACTION_TRACER, DST_TRANSACTION_EVENTS)

from newrelic.common.streaming_utils import SpanProtoAttrs

try:
    from newrelic.core.infinite_tracing_pb2 import Span
except:
    pass

_TransactionNode = namedtuple('_TransactionNode',
        ['settings', 'path', 'type', 'group', 'base_name', 'name_for_metric',
        'port', 'request_uri', 'queue_start', 'start_time',
        'end_time', 'last_byte_time', 'response_time', 'total_time',
        'duration', 'exclusive', 'root', 'errors', 'slow_sql',
        'custom_events', 'apdex_t', 'suppress_apdex', 'custom_metrics', 'guid',
        'cpu_time', 'suppress_transaction_trace', 'client_cross_process_id',
        'referring_transaction_guid', 'record_tt', 'synthetics_resource_id',
        'synthetics_job_id', 'synthetics_monitor_id', 'synthetics_header',
        'is_part_of_cat', 'trip_id', 'path_hash', 'referring_path_hash',
        'alternate_path_hashes', 'trace_intrinsics', 'agent_attributes',
        'distributed_trace_intrinsics', 'user_attributes', 'priority',
        'sampled', 'parent_transport_duration', 'parent_span', 'parent_type',
        'parent_account', 'parent_app', 'parent_tx', 'parent_transport_type',
        'root_span_guid', 'trace_id', 'loop_time'])


class TransactionNode(_TransactionNode):

    """Class holding data corresponding to the root of the transaction. All
    the nodes of interest recorded for the transaction are held as a tree
    structure within the 'children' attribute.

    """

    def __new__(cls, *args, **kwargs):
        node = _TransactionNode.__new__(cls, *args, **kwargs)
        node.include_transaction_trace_request_uri = False
        return node

    def __hash__(self):
        return id(self)

    @property
    def string_table(self):
        result = getattr(self, '_string_table', None)
        if result is not None:
            return result
        self._string_table = StringTable()
        return self._string_table

    @property
    def name(self):
        return self.name_for_metric

    def time_metrics(self, stats):
        """Return a generator yielding the timed metrics for the
        top level web transaction as well as all the child nodes.

        """

        # TODO What to do about a transaction where the name is
        # None. In the PHP agent it replaces it with an
        # underscore for timed metrics and continues. For an
        # apdex metric the PHP agent ignores it however. For now
        # we just ignore it.

        if not self.base_name:
            return

        if self.type == 'WebTransaction':
            # Report time taken by request dispatcher. We don't
            # know upstream time distinct from actual request
            # time so can't report time exclusively in the
            # dispatcher.

            # TODO Technically could work this out with the
            # modifications in Apache/mod_wsgi to mark start of
            # the request. How though does that differ to queue
            # time. Need to clarify purpose of HttpDispatcher
            # and how the exclusive component would appear in
            # the overview graphs.

            yield TimeMetric(
                    name='HttpDispatcher',
                    scope='',
                    duration=self.response_time,
                    exclusive=None)

            # Upstream queue time within any web server front end.

            # TODO How is this different to the exclusive time
            # component for the dispatcher above.

            # TODO Not yet dealing with additional headers for
            # tracking time through multiple front ends.

            if self.queue_start != 0:
                queue_wait = self.start_time - self.queue_start
                if queue_wait < 0:
                    queue_wait = 0

                yield TimeMetric(
                        name='WebFrontend/QueueTime',
                        scope='',
                        duration=queue_wait,
                        exclusive=None)

        # Generate the full transaction metric.

        yield TimeMetric(
                name=self.path,
                scope='',
                duration=self.response_time,
                exclusive=self.exclusive)

        # Generate the rollup metric.

        if self.type != 'WebTransaction':
            rollup = '%s/all' % self.type
        else:
            rollup = self.type

        yield TimeMetric(
                name=rollup,
                scope='',
                duration=self.response_time,
                exclusive=self.exclusive)

        # Generate Unscoped Total Time metrics.

        if self.type == 'WebTransaction':
            metric_prefix = 'WebTransactionTotalTime'
            metric_suffix = 'Web'
        else:
            metric_prefix = 'OtherTransactionTotalTime'
            metric_suffix = 'Other'

        yield TimeMetric(
                name='%s/%s' % (metric_prefix, self.name_for_metric),
                scope='',
                duration=self.total_time,
                exclusive=self.total_time)

        yield TimeMetric(
                name=metric_prefix,
                scope='',
                duration=self.total_time,
                exclusive=self.total_time)

        # Generate Distributed Tracing metrics

        if self.settings.distributed_tracing.enabled:
            dt_tag = "%s/%s/%s/%s/all" % (
                self.parent_type or 'Unknown',
                self.parent_account or 'Unknown',
                self.parent_app or 'Unknown',
                self.parent_transport_type or 'Unknown')

            for bonus_tag in ('', metric_suffix):
                yield TimeMetric(
                    name="DurationByCaller/%s%s" % (dt_tag, bonus_tag),
                    scope='',
                    duration=self.duration,
                    exclusive=self.duration)

                if self.parent_transport_duration is not None:
                    yield TimeMetric(
                        name="TransportDuration/%s%s" % (dt_tag, bonus_tag),
                        scope='',
                        duration=self.parent_transport_duration,
                        exclusive=self.parent_transport_duration)

                if self.errors:
                    yield TimeMetric(
                        name='ErrorsByCaller/%s%s' % (dt_tag, bonus_tag),
                        scope='',
                        duration=0.0,
                        exclusive=None)

        # Generate Error metrics

        if self.errors:
            if False in (error.expected for error in self.errors):
                # Generate overall rollup metric indicating if errors present.
                yield TimeMetric(
                    name='Errors/all',
                    scope='',
                    duration=0.0,
                    exclusive=None)

                # Generate individual error metric for transaction.
                yield TimeMetric(
                    name='Errors/%s' % self.path,
                    scope='',
                    duration=0.0,
                    exclusive=None)

                # Generate rollup metric for WebTransaction errors.
                yield TimeMetric(
                    name='Errors/all%s' % metric_suffix,
                    scope='',
                    duration=0.0,
                    exclusive=None)
            else:
                yield TimeMetric(
                    name='ErrorsExpected/all',
                    scope='',
                    duration=0.0,
                    exclusive=None)

        # Now for the children.
        for child in self.root.children:
            for metric in child.time_metrics(stats, self, self):
                yield metric

    def apdex_metrics(self, stats):
        """Return a generator yielding the apdex metrics for this node.

        """

        if not self.base_name:
            return

        if self.suppress_apdex:
            return

        # The apdex metrics are only relevant to web transactions.

        if self.type != 'WebTransaction':
            return

        # The magic calculations based on apdex_t. The apdex_t
        # is based on what was in place at the start of the
        # transaction. This could have changed between that
        # point in the request and now.

        satisfying = 0
        tolerating = 0
        frustrating = 0

        if self.errors and False in (error.expected for error in self.errors):
            frustrating = 1
        else:
            if self.duration <= self.apdex_t:
                satisfying = 1
            elif self.duration <= 4 * self.apdex_t:
                tolerating = 1
            else:
                frustrating = 1

        # Generate the full apdex metric.

        yield ApdexMetric(
                name='Apdex/%s' % self.name_for_metric,
                satisfying=satisfying,
                tolerating=tolerating,
                frustrating=frustrating,
                apdex_t=self.apdex_t)

        # Generate the rollup metric.

        yield ApdexMetric(
                name='Apdex',
                satisfying=satisfying,
                tolerating=tolerating,
                frustrating=frustrating,
                apdex_t=self.apdex_t)

    def error_details(self):
        """Return a generator yielding the details for each unique error
        captured during this transaction.

        """

        # TODO There is no attempt so far to eliminate duplicates.
        # Duplicates could be eliminated based on exception type
        # and message or exception type and file name/line number
        # presuming the latter are available. Right now the file
        # name and line number aren't captured so can't rely on it.

        # TODO There are no constraints in place on what keys/values
        # can be in params dictionaries. Need to convert values to
        # strings at some point.

        if not self.errors:
            return

        for error in self.errors:
            params = {}
            params["stack_trace"] = error.stack_trace

            intrinsics = {'spanId': error.span_id, 'error.expected': error.expected}
            intrinsics.update(self.trace_intrinsics)
            params['intrinsics'] = intrinsics

            params['agentAttributes'] = {}
            for attr in self.agent_attributes:
                if attr.destinations & DST_ERROR_COLLECTOR:
                    params['agentAttributes'][attr.name] = attr.value

            params['userAttributes'] = {}
            for attr in self.user_attributes:
                if attr.destinations & DST_ERROR_COLLECTOR:
                    params['userAttributes'][attr.name] = attr.value

            # add error specific custom params to this error's userAttributes

            err_attrs = create_user_attributes(error.custom_params,
                    self.settings.attribute_filter)
            for attr in err_attrs:
                if attr.destinations & DST_ERROR_COLLECTOR:
                    params['userAttributes'][attr.name] = attr.value

            yield newrelic.core.error_collector.TracedError(
                    start_time=error.timestamp,
                    path=self.path,
                    message=error.message,
                    type=error.type,
                    parameters=params)

    def transaction_trace(self, stats, limit, connections):

        self.trace_node_count = 0
        self.trace_node_limit = limit

        start_time = newrelic.core.trace_node.root_start_time(self)

        trace_node = self.root.trace_node(stats, self, connections)

        attributes = {}

        attributes['intrinsics'] = self.trace_intrinsics

        attributes['agentAttributes'] = {}
        for attr in self.agent_attributes:
            if attr.destinations & DST_TRANSACTION_TRACER:
                attributes['agentAttributes'][attr.name] = attr.value
                if attr.name == 'request.uri':
                    self.include_transaction_trace_request_uri = True

        attributes['userAttributes'] = {}
        for attr in self.user_attributes:
            if attr.destinations & DST_TRANSACTION_TRACER:
                attributes['userAttributes'][attr.name] = attr.value

        # There is an additional trace node labeled as 'ROOT'
        # that needs to be inserted below the root node object
        # which is returned. It inherits the start and end time
        # from the actual top node for the transaction.

        root = newrelic.core.trace_node.TraceNode(
                start_time=trace_node.start_time,
                end_time=trace_node.end_time,
                name='ROOT',
                params={},
                children=[trace_node],
                label=None)

        return newrelic.core.trace_node.RootNode(
                start_time=start_time,
                empty0={},
                empty1={},
                root=root,
                attributes=attributes)

    def slow_sql_nodes(self, stats):
        for item in self.slow_sql:
            yield item.slow_sql_node(stats, self)

    def apdex_perf_zone(self):
        """Return the single letter representation of an apdex perf zone."""

        # Apdex is only valid for WebTransactions.

        if self.type != 'WebTransaction':
            return None

        if self.errors and False in (error.expected for error in self.errors):
            return 'F'
        else:
            if self.duration <= self.apdex_t:
                return 'S'
            elif self.duration <= 4 * self.apdex_t:
                return 'T'
            else:
                return 'F'

    def transaction_event(self, stats_table):
        # Create the transaction event, which is a list of attributes.

        # Intrinsic attributes don't get filtered

        intrinsics = self.transaction_event_intrinsics(stats_table)

        # Add user and agent attributes to event

        user_attributes = {}
        for attr in self.user_attributes:
            if attr.destinations & DST_TRANSACTION_EVENTS:
                user_attributes[attr.name] = attr.value

        agent_attributes = {}
        for attr in self.agent_attributes:
            if attr.destinations & DST_TRANSACTION_EVENTS:
                agent_attributes[attr.name] = attr.value

        transaction_event = [intrinsics, user_attributes, agent_attributes]
        return transaction_event

    def transaction_event_intrinsics(self, stats_table):
        """Put together the intrinsic attributes for a transaction event"""

        intrinsics = self._event_intrinsics(stats_table)

        intrinsics['type'] = 'Transaction'
        intrinsics['name'] = self.path
        intrinsics['totalTime'] = self.total_time

        def _add_if_not_empty(key, value):
            if value:
                intrinsics[key] = value

        if self.errors:
            intrinsics['error'] = True

        if self.path_hash:
            intrinsics['nr.guid'] = self.guid
            intrinsics['nr.tripId'] = self.trip_id
            intrinsics['nr.pathHash'] = self.path_hash

            _add_if_not_empty('nr.referringPathHash',
                    self.referring_path_hash)
            _add_if_not_empty('nr.alternatePathHashes',
                    ','.join(self.alternate_path_hashes))
            _add_if_not_empty('nr.referringTransactionGuid',
                    self.referring_transaction_guid)
            _add_if_not_empty('nr.apdexPerfZone',
                    self.apdex_perf_zone())

        if self.synthetics_resource_id:
            intrinsics['nr.guid'] = self.guid

        if self.parent_tx:
            intrinsics['parentId'] = self.parent_tx

        if self.parent_span:
            intrinsics['parentSpanId'] = self.parent_span

        return intrinsics

    def error_events(self, stats_table):

        errors = []
        for error in self.errors:

            intrinsics = self.error_event_intrinsics(error, stats_table)

            # Add user and agent attributes to event

            agent_attributes = {}
            for attr in self.agent_attributes:
                if attr.destinations & DST_ERROR_COLLECTOR:
                    agent_attributes[attr.name] = attr.value

            user_attributes = {}
            for attr in self.user_attributes:
                if attr.destinations & DST_ERROR_COLLECTOR:
                    user_attributes[attr.name] = attr.value

            # add error specific custom params to this error's userAttributes

            err_attrs = create_user_attributes(error.custom_params,
                    self.settings.attribute_filter)
            for attr in err_attrs:
                if attr.destinations & DST_ERROR_COLLECTOR:
                    user_attributes[attr.name] = attr.value

            error_event = [intrinsics, user_attributes, agent_attributes]
            errors.append(error_event)

        return errors

    def error_event_intrinsics(self, error, stats_table):

        intrinsics = self._event_intrinsics(stats_table)

        intrinsics['type'] = "TransactionError"
        intrinsics['error.class'] = error.type
        intrinsics['error.message'] = error.message
        intrinsics['error.expected'] = error.expected
        intrinsics['transactionName'] = self.path
        intrinsics['spanId'] = error.span_id

        intrinsics['nr.transactionGuid'] = self.guid
        if self.referring_transaction_guid:
            guid = self.referring_transaction_guid
            intrinsics['nr.referringTransactionGuid'] = guid

        return intrinsics

    def _event_intrinsics(self, stats_table):
        """Common attributes for analytics events"""

        cache = getattr(self, '_event_intrinsics_cache', None)
        if cache is not None:

            # We don't want to execute this function more than once, since
            # it should always yield the same data per transaction

            return self._event_intrinsics_cache.copy()

        intrinsics = self.distributed_trace_intrinsics.copy()

        intrinsics['timestamp'] = int(1000.0 * self.start_time)
        intrinsics['duration'] = self.response_time

        if self.port:
            intrinsics['port'] = self.port

        # Add the Synthetics attributes to the intrinsics dict.

        if self.synthetics_resource_id:
            intrinsics['nr.syntheticsResourceId'] = self.synthetics_resource_id
            intrinsics['nr.syntheticsJobId'] = self.synthetics_job_id
            intrinsics['nr.syntheticsMonitorId'] = self.synthetics_monitor_id

        def _add_call_time(source, target):
            # include time for keys previously added to stats table via
            # stats_engine.record_transaction
            if (source, '') in stats_table:
                call_time = stats_table[(source, '')].total_call_time
                if target in intrinsics:
                    intrinsics[target] += call_time
                else:
                    intrinsics[target] = call_time

        def _add_call_count(source, target):
            # include counts for keys previously added to stats table via
            # stats_engine.record_transaction
            if (source, '') in stats_table:
                call_count = stats_table[(source, '')].call_count
                if target in intrinsics:
                    intrinsics[target] += call_count
                else:
                    intrinsics[target] = call_count

        _add_call_time('WebFrontend/QueueTime', 'queueDuration')

        _add_call_time('External/all', 'externalDuration')
        _add_call_time('Datastore/all', 'databaseDuration')
        _add_call_time('Memcache/all', 'memcacheDuration')

        _add_call_count('External/all', 'externalCallCount')
        _add_call_count('Datastore/all', 'databaseCallCount')

        if self.loop_time:
            intrinsics['eventLoopTime'] = self.loop_time
        _add_call_time('EventLoop/Wait/all', 'eventLoopWait')

        self._event_intrinsics_cache = intrinsics.copy()

        return intrinsics

    def span_protos(self, settings):
        for i_attrs, u_attrs, a_attrs in self.span_events(
                    settings, attr_class=SpanProtoAttrs):
            yield Span(trace_id=self.trace_id,
                       intrinsics=i_attrs,
                       user_attributes=u_attrs,
                       agent_attributes=a_attrs)

    def span_events(self, settings, attr_class=dict):
        base_attrs = attr_class((
            ('transactionId', self.guid),
            ('traceId', self.trace_id),
            ('sampled', self.sampled),
            ('priority', self.priority),
        ))

        for event in self.root.span_events(
            settings,
            base_attrs,
            parent_guid=self.parent_span,
            attr_class=attr_class,
        ):
            yield event
