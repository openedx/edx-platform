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

from __future__ import print_function

import logging
import os
import random
import re
import sys
import threading
import time
import warnings
import weakref
from collections import OrderedDict

import newrelic.core.database_node
import newrelic.core.error_node
import newrelic.core.root_node
import newrelic.core.transaction_node
import newrelic.packages.six as six
from newrelic.api.time_trace import TimeTrace
from newrelic.common.encoding_utils import (
    DistributedTracePayload,
    NrTraceState,
    W3CTraceParent,
    W3CTraceState,
    base64_decode,
    convert_to_cat_metadata_value,
    deobfuscate,
    ensure_str,
    generate_path_hash,
    json_decode,
    json_encode,
    obfuscate,
)
from newrelic.core.attribute import (
    MAX_NUM_USER_ATTRIBUTES,
    create_agent_attributes,
    create_attributes,
    create_user_attributes,
    process_user_attribute,
)
from newrelic.core.attribute_filter import (
    DST_ERROR_COLLECTOR,
    DST_NONE,
    DST_TRANSACTION_TRACER,
)
from newrelic.core.config import DEFAULT_RESERVOIR_SIZE
from newrelic.core.custom_event import create_custom_event
from newrelic.core.stack_trace import exception_stack
from newrelic.core.stats_engine import CustomMetrics, SampledDataSet
from newrelic.core.thread_utilization import utilization_tracker
from newrelic.core.trace_cache import (
    TraceCacheActiveTraceError,
    TraceCacheNoActiveTraceError,
    trace_cache,
)

_logger = logging.getLogger(__name__)

DISTRIBUTED_TRACE_KEYS_REQUIRED = ("ty", "ac", "ap", "tr", "ti")
DISTRIBUTED_TRACE_TRANSPORT_TYPES = set(("HTTP", "HTTPS", "Kafka", "JMS", "IronMQ", "AMQP", "Queue", "Other"))
DELIMITER_FORMAT_RE = re.compile("[ \t]*,[ \t]*")
ACCEPTED_DISTRIBUTED_TRACE = 1
CREATED_DISTRIBUTED_TRACE = 2
PARENT_TYPE = {
    "0": "App",
    "1": "Browser",
    "2": "Mobile",
}


class Sentinel(TimeTrace):
    def __init__(self, transaction):
        super(Sentinel, self).__init__(None)
        self.transaction = transaction

        # Set the thread id to the same as the transaction
        self.thread_id = transaction.thread_id

    def add_child(self, node):
        self.children.append(node)

    def update_with_transaction_custom_attributes(self, transaction_params):
        """
        Loops through the transaction attributes and adds them to the
        root span's user attributes.
        """
        for key, value in transaction_params.items():
            if len(self.user_attributes) >= MAX_NUM_USER_ATTRIBUTES:
                _logger.debug(
                    "Maximum number of custom attributes already "
                    "added to span. Some transaction attributes may "
                    "not be included."
                )
                break
            if key not in self.user_attributes:
                self.user_attributes[key] = value

    def complete_root(self):
        try:
            trace_cache().complete_root(self)
        finally:
            self.exited = True

    @staticmethod
    def complete_trace():
        pass

    @property
    def transaction(self):
        return self._transaction and self._transaction()

    @transaction.setter
    def transaction(self, value):
        if value:
            self._transaction = weakref.ref(value)

    @property
    def root(self):
        return self

    @root.setter
    def root(self, value):
        pass


class CachedPath(object):
    def __init__(self, transaction):
        self._name = None
        self.transaction = weakref.ref(transaction)

    def path(self):
        if self._name is not None:
            return self._name

        transaction = self.transaction()
        if transaction:
            return transaction.path

        return "Unknown"


class Transaction(object):

    STATE_PENDING = 0
    STATE_RUNNING = 1
    STATE_STOPPED = 2

    def __init__(self, application, enabled=None):

        self._application = application

        self.thread_id = None

        self._transaction_id = id(self)
        self._transaction_lock = threading.Lock()

        self._dead = False

        self._state = self.STATE_PENDING
        self._settings = None

        self._name_priority = 0
        self._group = None
        self._name = None
        self._cached_path = CachedPath(self)
        self._loop_time = 0.0

        self._frameworks = set()

        self._frozen_path = None

        self.root_span = None

        self._request_uri = None
        self._port = None

        self.queue_start = 0.0

        self.start_time = 0.0
        self.end_time = 0.0
        self.last_byte_time = 0.0

        self.total_time = 0.0

        self.stopped = False

        self._trace_node_count = 0

        self._errors = []
        self._slow_sql = []
        self._custom_events = SampledDataSet(capacity=DEFAULT_RESERVOIR_SIZE)

        self._stack_trace_count = 0
        self._explain_plan_count = 0

        self._string_cache = {}

        self._custom_params = OrderedDict()
        self._request_params = {}

        self._utilization_tracker = None

        self._thread_utilization_start = None
        self._thread_utilization_end = None
        self._thread_utilization_value = None

        self._cpu_user_time_start = None
        self._cpu_user_time_end = None
        self._cpu_user_time_value = 0.0

        self._read_length = None

        self._read_start = None
        self._read_end = None

        self._sent_start = None
        self._sent_end = None

        self._bytes_read = 0
        self._bytes_sent = 0

        self._calls_read = 0
        self._calls_readline = 0
        self._calls_readlines = 0

        self._calls_write = 0
        self._calls_yield = 0

        self._transaction_metrics = {}

        self._agent_attributes = {}

        self.background_task = False

        self.enabled = False
        self.autorum_disabled = False

        self.ignore_transaction = False
        self.suppress_apdex = False
        self.suppress_transaction_trace = False

        self.capture_params = None

        self.apdex = 0

        self.rum_token = None

        trace_id = "%032x" % random.getrandbits(128)

        # 16-digit random hex. Padded with zeros in the front.
        self.guid = trace_id[:16]

        # 32-digit random hex. Padded with zeros in the front.
        self._trace_id = trace_id

        # This may be overridden by processing an inbound CAT header
        self.parent_type = None
        self.parent_span = None
        self.trusted_parent_span = None
        self.tracing_vendors = None
        self.parent_tx = None
        self.parent_app = None
        self.parent_account = None
        self.parent_transport_type = None
        self.parent_transport_duration = None
        self.tracestate = ""
        self._priority = None
        self._sampled = None

        self._distributed_trace_state = 0

        self.client_cross_process_id = None
        self.client_account_id = None
        self.client_application_id = None
        self.referring_transaction_guid = None
        self.record_tt = False
        self._trip_id = None
        self._referring_path_hash = None
        self._alternate_path_hashes = {}
        self.is_part_of_cat = False

        self.synthetics_resource_id = None
        self.synthetics_job_id = None
        self.synthetics_monitor_id = None
        self.synthetics_header = None

        self._custom_metrics = CustomMetrics()

        global_settings = application.global_settings

        if global_settings.enabled:
            if enabled or (enabled is None and application.enabled):
                self._settings = application.settings
                if not self._settings:
                    application.activate()

                    # We see again if the settings is now valid
                    # in case startup timeout had been specified
                    # and registration had been started and
                    # completed within the timeout.

                    self._settings = application.settings

                if self._settings:
                    self.enabled = True

    def __del__(self):
        self._dead = True
        if self._state == self.STATE_RUNNING:
            self.__exit__(None, None, None)

    def __enter__(self):

        assert self._state == self.STATE_PENDING

        # Bail out if the transaction is not enabled.

        if not self.enabled:
            return self

        # Record the start time for transaction.

        self.start_time = time.time()

        # Record initial CPU user time.

        self._cpu_user_time_start = os.times()[0]

        # Set the thread ID upon entering the transaction.
        # This is done here so that any asyncio tasks will
        # be active and the task ID will be used to
        # store traces into the trace cache.
        self.thread_id = trace_cache().current_thread_id()

        # Create the root span then push it
        # into the trace cache as the active trace.
        # If there is an active transaction already
        # mark this one as disabled and do not raise the
        # exception.
        self.root_span = root_span = Sentinel(self)

        try:
            trace_cache().save_trace(root_span)
        except TraceCacheActiveTraceError:
            self.enabled = False
            return self

        # Calculate initial thread utilisation factor.
        # For now we only do this if we know it is an
        # actual thread and not a greenlet.

        if not hasattr(sys, "_current_frames") or self.thread_id in sys._current_frames():
            try:
                thread_instance = threading.current_thread()
            except TypeError:
                thread_instance = threading.currentThread()

            self._utilization_tracker = utilization_tracker(self.application.name)
            if self._utilization_tracker:
                self._utilization_tracker.enter_transaction(thread_instance)
                self._thread_utilization_start = self._utilization_tracker.utilization_count()

        # Mark transaction as active and update state
        # used to validate correct usage of class.

        self._state = self.STATE_RUNNING

        return self

    def __exit__(self, exc, value, tb):

        # Bail out if the transaction is not enabled.

        if not self.enabled:
            return

        if self._transaction_id != id(self):
            return

        if not self._settings:
            return

        # Record error if one was registered.

        if exc is not None and value is not None and tb is not None:
            self.root_span.notice_error((exc, value, tb))

        self._state = self.STATE_STOPPED

        # Force the root span out of the cache if it's there
        # This also prevents saving of the root span in the future since the
        # transaction will be None
        root = self.root_span
        try:
            root.complete_root()
        except TraceCacheNoActiveTraceError:
            # It's possible that the weakref can be cleared prior to a
            # finalizer call. This results in traces being implicitly dropped
            # from the cache even though they're still referenced at this time.
            #
            # https://bugs.python.org/issue40312
            if not self._dead:
                _logger.exception(
                    "Runtime instrumentation error. Attempt to "
                    "drop the trace but where none is active. "
                    "Report this issue to New Relic support."
                ),
                return
        except Exception:
            _logger.exception(
                "Runtime instrumentation error. Exception "
                "occurred during exit. Report this issue to New Relic support."
            )
            return

        # Record the end time for transaction and then
        # calculate the duration.

        if not self.stopped:
            self.end_time = time.time()

        # Calculate transaction duration

        duration = self.end_time - self.start_time

        # Calculate response time. Calculation depends on whether
        # a web response was sent back.

        if self.last_byte_time == 0.0:
            response_time = duration
        else:
            response_time = self.last_byte_time - self.start_time

        # Calculate overall user time.

        if not self._cpu_user_time_end:
            self._cpu_user_time_end = os.times()[0]

        if duration and self._cpu_user_time_end:
            self._cpu_user_time_value = self._cpu_user_time_end - self._cpu_user_time_start

        # Calculate thread utilisation factor. Note that even if
        # we are tracking thread utilization we skip calculation
        # if duration is zero. Under normal circumstances this
        # should not occur but may if the system clock is wound
        # backwards and duration was squashed to zero due to the
        # request appearing to finish before it started. It may
        # also occur if true response time came in under the
        # resolution of the clock being used, but that is highly
        # unlikely as the overhead of the agent itself should
        # always ensure that that is hard to achieve.

        if self._utilization_tracker:
            self._utilization_tracker.exit_transaction()
            if self._thread_utilization_start is not None and duration > 0.0:
                if not self._thread_utilization_end:
                    self._thread_utilization_end = self._utilization_tracker.utilization_count()
                self._thread_utilization_value = (
                    self._thread_utilization_end - self._thread_utilization_start
                ) / duration

        self._freeze_path()

        # _sent_end should already be set by this point, but in case it
        # isn't, set it now before we record the custom metrics and derive
        # agent attributes

        if self._sent_start:
            if not self._sent_end:
                self._sent_end = time.time()

        request_params = self.request_parameters

        root.update_with_transaction_custom_attributes(self._custom_params)

        # Update agent attributes and include them on the root node
        self._update_agent_attributes()
        root_agent_attributes = dict(self._agent_attributes)
        root_agent_attributes.update(request_params)
        root_agent_attributes.update(root.agent_attributes)

        exclusive = duration + root.exclusive

        root_node = newrelic.core.root_node.RootNode(
            name=self.name_for_metric,
            children=tuple(root.children),
            start_time=self.start_time,
            end_time=self.end_time,
            exclusive=exclusive,
            duration=duration,
            guid=root.guid,
            agent_attributes=root_agent_attributes,
            user_attributes=root.user_attributes,
            path=self.path,
            trusted_parent_span=self.trusted_parent_span,
            tracing_vendors=self.tracing_vendors,
        )

        # Add transaction exclusive time to total exclusive time
        #
        self.total_time += exclusive

        if self.client_cross_process_id is not None:
            metric_name = "ClientApplication/%s/all" % (self.client_cross_process_id)
            self.record_custom_metric(metric_name, duration)

        # Record supportability metrics for api calls

        for key, value in six.iteritems(self._transaction_metrics):
            self.record_custom_metric(key, {"count": value})

        if self._frameworks:
            for framework, version in self._frameworks:
                self.record_custom_metric("Python/Framework/%s/%s" % (framework, version), 1)

        if self._settings.distributed_tracing.enabled:
            # Sampled and priority need to be computed at the end of the
            # transaction when distributed tracing or span events are enabled.
            self._compute_sampled_and_priority()

        self._cached_path._name = self.path
        agent_attributes = self.agent_attributes
        agent_attributes.extend(self.filter_request_parameters(request_params))
        node = newrelic.core.transaction_node.TransactionNode(
            settings=self._settings,
            path=self.path,
            type=self.type,
            group=self.group_for_metric,
            base_name=self._name,
            name_for_metric=self.name_for_metric,
            port=self._port,
            request_uri=self._request_uri,
            queue_start=self.queue_start,
            start_time=self.start_time,
            end_time=self.end_time,
            last_byte_time=self.last_byte_time,
            total_time=self.total_time,
            response_time=response_time,
            duration=duration,
            exclusive=exclusive,
            errors=tuple(self._errors),
            slow_sql=tuple(self._slow_sql),
            custom_events=self._custom_events,
            apdex_t=self.apdex,
            suppress_apdex=self.suppress_apdex,
            custom_metrics=self._custom_metrics,
            guid=self.guid,
            cpu_time=self._cpu_user_time_value,
            suppress_transaction_trace=self.suppress_transaction_trace,
            client_cross_process_id=self.client_cross_process_id,
            referring_transaction_guid=self.referring_transaction_guid,
            record_tt=self.record_tt,
            synthetics_resource_id=self.synthetics_resource_id,
            synthetics_job_id=self.synthetics_job_id,
            synthetics_monitor_id=self.synthetics_monitor_id,
            synthetics_header=self.synthetics_header,
            is_part_of_cat=self.is_part_of_cat,
            trip_id=self.trip_id,
            path_hash=self.path_hash,
            referring_path_hash=self._referring_path_hash,
            alternate_path_hashes=self.alternate_path_hashes,
            trace_intrinsics=self.trace_intrinsics,
            distributed_trace_intrinsics=self.distributed_trace_intrinsics,
            agent_attributes=agent_attributes,
            user_attributes=self.user_attributes,
            priority=self.priority,
            sampled=self.sampled,
            parent_span=self.parent_span,
            parent_transport_duration=self.parent_transport_duration,
            parent_type=self.parent_type,
            parent_account=self.parent_account,
            parent_app=self.parent_app,
            parent_tx=self.parent_tx,
            parent_transport_type=self.parent_transport_type,
            root_span_guid=root.guid,
            trace_id=self.trace_id,
            loop_time=self._loop_time,
            root=root_node,
        )

        # Clear settings as we are all done and don't need it
        # anymore.

        self._settings = None
        self.enabled = False

        # Unless we are ignoring the transaction, record it. We
        # need to lock the profile samples and replace it with
        # an empty list just in case the thread profiler kicks
        # in just as we are trying to record the transaction.
        # If we don't, when processing the samples, addition of
        # new samples can cause an error.

        if not self.ignore_transaction:

            self._application.record_transaction(node)

    @property
    def sampled(self):
        return self._sampled

    @property
    def priority(self):
        return self._priority

    @property
    def state(self):
        return self._state

    @property
    def is_distributed_trace(self):
        return self._distributed_trace_state != 0

    @property
    def settings(self):
        return self._settings

    @property
    def application(self):
        return self._application

    @property
    def type(self):
        if self.background_task:
            transaction_type = "OtherTransaction"
        else:
            transaction_type = "WebTransaction"
        return transaction_type

    @property
    def name(self):
        return self._name

    @property
    def group(self):
        return self._group

    @property
    def name_for_metric(self):
        """Combine group and name for use as transaction name in metrics."""
        group = self.group_for_metric

        transaction_name = self._name

        if transaction_name is None:
            transaction_name = "<undefined>"

        # Stripping the leading slash on the request URL held by
        # transaction_name when type is 'Uri' is to keep compatibility
        # with PHP agent and also possibly other agents. Leading
        # slash it not deleted for other category groups as the
        # leading slash may be significant in that situation.

        if group in ("Uri", "NormalizedUri") and transaction_name.startswith("/"):
            name = "%s%s" % (group, transaction_name)
        else:
            name = "%s/%s" % (group, transaction_name)

        return name

    @property
    def group_for_metric(self):
        _group = self._group

        if _group is None:
            if self.background_task:
                _group = "Python"
            else:
                _group = "Uri"

        return _group

    @property
    def path(self):
        if self._frozen_path:
            return self._frozen_path

        return "%s/%s" % (self.type, self.name_for_metric)

    @property
    def trip_id(self):
        return self._trip_id or self.guid

    @property
    def trace_id(self):
        return self._trace_id

    @property
    def alternate_path_hashes(self):
        """Return the alternate path hashes but not including the current path
        hash.

        """
        return sorted(set(self._alternate_path_hashes.values()) - set([self.path_hash]))

    @property
    def path_hash(self):
        """Path hash is a 32-bit digest of the string "appname;txn_name"
        XORed with the referring_path_hash. Since the txn_name can change
        during the course of a transaction, up to 10 path_hashes are stored
        in _alternate_path_hashes. Before generating the path hash, check the
        _alternate_path_hashes to determine if we've seen this identifier and
        return the value.

        """

        if not self.is_part_of_cat:
            return None

        identifier = "%s;%s" % (self.application.name, self.path)

        # Check if identifier is already part of the _alternate_path_hashes and
        # return the value if available.

        if self._alternate_path_hashes.get(identifier):
            return self._alternate_path_hashes[identifier]

        # If the referring_path_hash is unavailable then we use '0' as the
        # seed.

        try:
            seed = int((self._referring_path_hash or "0"), base=16)
        except Exception:
            seed = 0

        try:
            path_hash = generate_path_hash(identifier, seed)
        except ValueError:
            _logger.warning(
                "Unable to generate cross application tracer headers. "
                "MD5 hashing may not be available. (Is this system FIPS compliant?) "
                "We recommend enabling distributed tracing instead. For details and a transition guide see "
                "https://docs.newrelic.com/docs/agents/python-agent/configuration/python-agent-configuration#distributed-tracing-settings"
            )
            return None

        # Only store up to 10 alternate path hashes.

        if len(self._alternate_path_hashes) < 10:
            self._alternate_path_hashes[identifier] = path_hash

        return path_hash

    @property
    def attribute_filter(self):
        return self._settings.attribute_filter

    @property
    def read_duration(self):
        read_duration = 0
        if self._read_start and self._read_end:
            read_duration = self._read_end - self._read_start
        return read_duration

    @property
    def sent_duration(self):
        sent_duration = 0
        if self._sent_start and self._sent_end:
            sent_duration = self._sent_end - self._sent_start
        return sent_duration

    @property
    def queue_wait(self):
        queue_wait = 0
        if self.queue_start:
            queue_wait = self.start_time - self.queue_start
            if queue_wait < 0:
                queue_wait = 0
        return queue_wait

    @property
    def should_record_segment_params(self):
        # Only record parameters when it is safe to do so
        return self.settings and not self.settings.high_security

    @property
    def trace_intrinsics(self):
        """Intrinsic attributes for transaction traces and error traces"""
        i_attrs = {}

        if self.referring_transaction_guid:
            i_attrs["referring_transaction_guid"] = self.referring_transaction_guid
        if self.client_cross_process_id:
            i_attrs["client_cross_process_id"] = self.client_cross_process_id
        if self.trip_id:
            i_attrs["trip_id"] = self.trip_id
        if self.path_hash:
            i_attrs["path_hash"] = self.path_hash
        if self.synthetics_resource_id:
            i_attrs["synthetics_resource_id"] = self.synthetics_resource_id
        if self.synthetics_job_id:
            i_attrs["synthetics_job_id"] = self.synthetics_job_id
        if self.synthetics_monitor_id:
            i_attrs["synthetics_monitor_id"] = self.synthetics_monitor_id
        if self.total_time:
            i_attrs["totalTime"] = self.total_time
        if self._loop_time:
            i_attrs["eventLoopTime"] = self._loop_time

        # Add in special CPU time value for UI to display CPU burn.

        # XXX Disable cpu time value for CPU burn as was
        # previously reporting incorrect value and we need to
        # fix it, at least on Linux to report just the CPU time
        # for the executing thread.

        # if self._cpu_user_time_value:
        #     i_attrs['cpu_time'] = self._cpu_user_time_value

        i_attrs.update(self.distributed_trace_intrinsics)

        return i_attrs

    @property
    def distributed_trace_intrinsics(self):
        i_attrs = {}

        if not self._settings.distributed_tracing.enabled:
            return i_attrs

        i_attrs["guid"] = self.guid
        i_attrs["sampled"] = self.sampled
        i_attrs["priority"] = self.priority
        i_attrs["traceId"] = self.trace_id

        if not self._distributed_trace_state:
            return i_attrs

        if self.parent_type:
            i_attrs["parent.type"] = self.parent_type
        if self.parent_account:
            i_attrs["parent.account"] = self.parent_account
        if self.parent_app:
            i_attrs["parent.app"] = self.parent_app
        if self.parent_transport_type:
            i_attrs["parent.transportType"] = self.parent_transport_type
        if self.parent_transport_duration:
            i_attrs["parent.transportDuration"] = self.parent_transport_duration
        if self.trusted_parent_span:
            i_attrs["trustedParentId"] = self.trusted_parent_span
        if self.tracing_vendors:
            i_attrs["tracingVendors"] = self.tracing_vendors

        return i_attrs

    def filter_request_parameters(self, params):
        # Request parameters are a special case of agent attributes, so
        # they must be filtered separately

        # There are 3 cases we need to handle:
        #
        # 1. LEGACY: capture_params = False
        #
        #    Don't add request parameters at all, which means they will not
        #    go through the AttributeFilter.
        #
        # 2. LEGACY: capture_params = True
        #
        #    Filter request parameters through the AttributeFilter, but
        #    set the destinations to `TRANSACTION_TRACER | ERROR_COLLECTOR`.
        #
        #    If the user does not add any additional attribute filtering
        #    rules, this will result in the same outcome as the old
        #    capture_params = True behavior. They will be added to transaction
        #    traces and error traces.
        #
        # 3. CURRENT: capture_params is None
        #
        #    Filter request parameters through the AttributeFilter, but set
        #    the destinations to NONE.
        #
        #    That means by default, request parameters won't get included in
        #    any destination. But, it will allow user added include/exclude
        #    attribute filtering rules to be applied to the request parameters.
        attributes_request = []

        if self.capture_params is None:
            attributes_request = create_attributes(params, DST_NONE, self.attribute_filter)
        elif self.capture_params:
            attributes_request = create_attributes(
                params, DST_ERROR_COLLECTOR | DST_TRANSACTION_TRACER, self.attribute_filter
            )
        return attributes_request

    @property
    def request_parameters(self):
        if (self.capture_params is None) or self.capture_params:

            if self._request_params:

                r_attrs = {}

                for k, v in self._request_params.items():
                    new_key = "request.parameters.%s" % k
                    new_val = ",".join(v)

                    final_key, final_val = process_user_attribute(new_key, new_val)

                    if final_key:
                        r_attrs[final_key] = final_val

                return r_attrs
        return {}

    def _add_agent_attribute(self, key, value):
        self._agent_attributes[key] = value

    @property
    def agent_attributes(self):
        agent_attributes = create_agent_attributes(self._agent_attributes, self.attribute_filter)
        return agent_attributes

    def _update_agent_attributes(self):
        a_attrs = self._agent_attributes

        if self._settings.process_host.display_name:
            a_attrs["host.displayName"] = self._settings.process_host.display_name
        if self._thread_utilization_value:
            a_attrs["thread.concurrency"] = self._thread_utilization_value
        if self.queue_wait != 0:
            a_attrs["webfrontend.queue.seconds"] = self.queue_wait

    @property
    def user_attributes(self):
        return create_user_attributes(self._custom_params, self.attribute_filter)

    def _compute_sampled_and_priority(self):
        if self._priority is None:
            # truncate priority field to 6 digits past the decimal
            self._priority = float("%.6f" % random.random())  # nosec

        if self._sampled is None:
            self._sampled = self._application.compute_sampled()
            if self._sampled:
                self._priority += 1

    def _freeze_path(self):
        if self._frozen_path is None:
            self._name_priority = None

            if self._group == "Uri" and self._name != "/":
                # Apply URL normalization rules. We would only have raw
                # URLs where we were not specifically naming the web
                # transactions for a specific web framework to be a code
                # handler or otherwise.

                name, ignore = self._application.normalize_name(self._name, "url")

                if self._name != name:
                    self._group = "NormalizedUri"
                    self._name = name

                self.ignore_transaction = self.ignore_transaction or ignore

            # Apply transaction rules on the full transaction name.

            path, ignore = self._application.normalize_name(self.path, "transaction")

            self.ignore_transaction = self.ignore_transaction or ignore

            # Apply segment whitelist rule to the segments on the full
            # transaction name. The path is frozen at this point and cannot be
            # further changed.

            self._frozen_path, ignore = self._application.normalize_name(path, "segment")

            self.ignore_transaction = self.ignore_transaction or ignore

            # Look up the apdex from the table of key transactions. If
            # current transaction is not a key transaction then use the
            # default apdex from settings. The path used at this point
            # is the frozen path.

            self.apdex = self._settings.web_transactions_apdex.get(self.path) or self._settings.apdex_t

    def _record_supportability(self, metric_name):
        m = self._transaction_metrics.get(metric_name, 0)
        self._transaction_metrics[metric_name] = m + 1

    def _create_distributed_trace_data_with_guid(self, guid):
        data = self._create_distributed_trace_data()
        if guid and data and "id" in data:
            data["id"] = guid
        return data

    def _create_distributed_trace_data(self):
        if not self.enabled:
            return

        settings = self._settings
        account_id = settings.account_id
        trusted_account_key = settings.trusted_account_key
        application_id = settings.primary_application_id

        if not (account_id and application_id and trusted_account_key and settings.distributed_tracing.enabled):
            return

        self._compute_sampled_and_priority()
        data = dict(
            ty="App",
            ac=account_id,
            ap=application_id,
            tr=self.trace_id,
            sa=self.sampled,
            pr=self.priority,
            tx=self.guid,
            ti=int(time.time() * 1000.0),
        )

        if account_id != trusted_account_key:
            data["tk"] = trusted_account_key

        current_span = trace_cache().current_trace()
        if settings.span_events.enabled and settings.collect_span_events and current_span:
            data["id"] = current_span.guid

        self._distributed_trace_state |= CREATED_DISTRIBUTED_TRACE

        return data

    def _create_distributed_trace_payload(self):
        try:
            data = self._create_distributed_trace_data()
            if data is None:
                return
            payload = DistributedTracePayload(
                v=DistributedTracePayload.version,
                d=data,
            )
        except:
            self._record_supportability("Supportability/DistributedTrace/CreatePayload/Exception")
        else:
            self._record_supportability("Supportability/DistributedTrace/CreatePayload/Success")
            return payload

    def create_distributed_trace_payload(self):
        warnings.warn(
            (
                "The create_distributed_trace_payload API has been deprecated. "
                "Please use the insert_distributed_trace_headers API."
            ),
            DeprecationWarning,
        )
        return self._create_distributed_trace_payload()

    def _generate_distributed_trace_headers(self, data=None):
        try:
            data = data or self._create_distributed_trace_data()
            if data:

                traceparent = W3CTraceParent(data).text()
                yield ("traceparent", traceparent)

                tracestate = NrTraceState(data).text()
                if self.tracestate:
                    tracestate += "," + self.tracestate
                yield ("tracestate", tracestate)

                self._record_supportability("Supportability/TraceContext/Create/Success")

                if not self._settings.distributed_tracing.exclude_newrelic_header:
                    # Insert New Relic dt headers for backwards compatibility
                    payload = DistributedTracePayload(
                        v=DistributedTracePayload.version,
                        d=data,
                    )
                    yield ("newrelic", payload.http_safe())
                    self._record_supportability("Supportability/DistributedTrace/CreatePayload/Success")

        except:
            self._record_supportability("Supportability/TraceContext/Create/Exception")

            if not self._settings.distributed_tracing.exclude_newrelic_header:
                self._record_supportability("Supportability/DistributedTrace/CreatePayload/Exception")

    def insert_distributed_trace_headers(self, headers):
        headers.extend(self._generate_distributed_trace_headers())

    def _can_accept_distributed_trace_headers(self):
        if not self.enabled:
            return False

        settings = self._settings
        if not (settings.distributed_tracing.enabled and settings.trusted_account_key):
            return False

        if self._distributed_trace_state:
            if self._distributed_trace_state & ACCEPTED_DISTRIBUTED_TRACE:
                self._record_supportability("Supportability/DistributedTrace/AcceptPayload/Ignored/Multiple")
            else:
                self._record_supportability("Supportability/DistributedTrace/AcceptPayload/Ignored/CreateBeforeAccept")
            return False

        return True

    def _accept_distributed_trace_payload(self, payload, transport_type="HTTP"):
        if not payload:
            self._record_supportability("Supportability/DistributedTrace/AcceptPayload/Ignored/Null")
            return False

        payload = DistributedTracePayload.decode(payload)
        if not payload:
            self._record_supportability("Supportability/DistributedTrace/AcceptPayload/ParseException")
            return False

        try:
            version = payload.get("v")
            major_version = version and int(version[0])

            if major_version is None:
                self._record_supportability("Supportability/DistributedTrace/AcceptPayload/ParseException")
                return False

            if major_version > DistributedTracePayload.version[0]:
                self._record_supportability("Supportability/DistributedTrace/AcceptPayload/Ignored/MajorVersion")
                return False

            data = payload.get("d", {})
            if not all(k in data for k in DISTRIBUTED_TRACE_KEYS_REQUIRED):
                self._record_supportability("Supportability/DistributedTrace/AcceptPayload/ParseException")
                return False

            # Must have either id or tx
            if not any(k in data for k in ("id", "tx")):
                self._record_supportability("Supportability/DistributedTrace/AcceptPayload/ParseException")
                return False

            settings = self._settings
            account_id = data.get("ac")

            # If trust key doesn't exist in the payload, use account_id
            received_trust_key = data.get("tk", account_id)
            if settings.trusted_account_key != received_trust_key:
                self._record_supportability("Supportability/DistributedTrace/AcceptPayload/Ignored/UntrustedAccount")
                if settings.debug.log_untrusted_distributed_trace_keys:
                    _logger.debug(
                        "Received untrusted key in distributed trace payload. received_trust_key=%r",
                        received_trust_key,
                    )
                return False

            try:
                data["ti"] = int(data["ti"])
            except:
                return False

            if "pr" in data:
                try:
                    data["pr"] = float(data["pr"])
                except:
                    data["pr"] = None

            self._accept_distributed_trace_data(data, transport_type)
            self._record_supportability("Supportability/DistributedTrace/AcceptPayload/Success")
            return True

        except:
            self._record_supportability("Supportability/DistributedTrace/AcceptPayload/Exception")
            return False

    def accept_distributed_trace_payload(self, *args, **kwargs):
        warnings.warn(
            (
                "The accept_distributed_trace_payload API has been deprecated. "
                "Please use the accept_distributed_trace_headers API."
            ),
            DeprecationWarning,
        )
        if not self._can_accept_distributed_trace_headers():
            return False
        return self._accept_distributed_trace_payload(*args, **kwargs)

    def _accept_distributed_trace_data(self, data, transport_type):
        if transport_type not in DISTRIBUTED_TRACE_TRANSPORT_TYPES:
            transport_type = "Unknown"

        self.parent_transport_type = transport_type

        self.parent_type = data.get("ty")

        self.parent_span = data.get("id")
        self.parent_tx = data.get("tx")
        self.parent_app = data.get("ap")
        self.parent_account = data.get("ac")

        self._trace_id = data.get("tr")

        priority = data.get("pr")
        if priority is not None:
            self._priority = priority
            self._sampled = data.get("sa")

        if "ti" in data:
            transport_start = data["ti"] / 1000.0

            # If starting in the future, transport duration should be set to 0
            now = time.time()
            if transport_start > now:
                self.parent_transport_duration = 0.0
            else:
                self.parent_transport_duration = now - transport_start

        self._distributed_trace_state = ACCEPTED_DISTRIBUTED_TRACE

    def accept_distributed_trace_headers(self, headers, transport_type="HTTP"):
        if not self._can_accept_distributed_trace_headers():
            return False

        try:
            traceparent = headers.get("traceparent", "")
            tracestate = headers.get("tracestate", "")
            distributed_header = headers.get("newrelic", "")
        except Exception:
            traceparent = ""
            tracestate = ""
            distributed_header = ""

            for k, v in headers:
                k = ensure_str(k)
                if k == "traceparent":
                    traceparent = v
                elif k == "tracestate":
                    tracestate = v
                elif k == "newrelic":
                    distributed_header = v

        if traceparent:
            try:
                traceparent = ensure_str(traceparent).strip()
                data = W3CTraceParent.decode(traceparent)
            except:
                data = None

            if not data:
                self._record_supportability("Supportability/TraceContext/TraceParent/Parse/Exception")
                return False

            self._record_supportability("Supportability/TraceContext/TraceParent/Accept/Success")
            if tracestate:
                tracestate = ensure_str(tracestate)
                try:
                    vendors = W3CTraceState.decode(tracestate)
                    tk = self._settings.trusted_account_key
                    payload = vendors.pop(tk + "@nr", "")
                    self.tracing_vendors = ",".join(vendors.keys())
                    self.tracestate = vendors.text(limit=31)
                except:
                    self._record_supportability("Supportability/TraceContext/TraceState/Parse/Exception")
                else:
                    # Remove trusted new relic header if available and parse
                    if payload:
                        try:
                            tracestate_data = NrTraceState.decode(payload, tk)
                        except:
                            tracestate_data = None
                        if tracestate_data:
                            self.trusted_parent_span = tracestate_data.pop("id", None)
                            data.update(tracestate_data)
                        else:
                            self._record_supportability("Supportability/TraceContext/TraceState/InvalidNrEntry")
                    else:
                        self._record_supportability("Supportability/TraceContext/TraceState/NoNrEntry")

            self._accept_distributed_trace_data(data, transport_type)
            self._record_supportability("Supportability/TraceContext/Accept/Success")
            return True
        elif distributed_header:
            distributed_header = ensure_str(distributed_header)
            return self._accept_distributed_trace_payload(distributed_header, transport_type)

    def _process_incoming_cat_headers(self, encoded_cross_process_id, encoded_txn_header):
        settings = self._settings

        if not self.enabled:
            return

        if not (
            settings.cross_application_tracer.enabled
            and settings.cross_process_id
            and settings.trusted_account_ids
            and settings.encoding_key
        ):
            return

        if encoded_cross_process_id is None:
            return

        try:
            client_cross_process_id = deobfuscate(encoded_cross_process_id, settings.encoding_key)

            # The cross process ID consists of the client
            # account ID and the ID of the specific application
            # the client is recording requests against. We need
            # to validate that the client account ID is in the
            # list of trusted account IDs and ignore it if it
            # isn't. The trusted account IDs list has the
            # account IDs as integers, so save the client ones
            # away as integers here so easier to compare later.

            client_account_id, client_application_id = map(int, client_cross_process_id.split("#"))

            if client_account_id not in settings.trusted_account_ids:
                return

            self.client_cross_process_id = client_cross_process_id
            self.client_account_id = client_account_id
            self.client_application_id = client_application_id

            txn_header = json_decode(deobfuscate(encoded_txn_header, settings.encoding_key))

            if txn_header:
                self.is_part_of_cat = True
                self.referring_transaction_guid = txn_header[0]

                # Incoming record_tt is OR'd with existing
                # record_tt. In the scenario where we make multiple
                # ext request, this will ensure we don't set the
                # record_tt to False by a later request if it was
                # set to True by an earlier request.

                self.record_tt = self.record_tt or txn_header[1]

                if isinstance(txn_header[2], six.string_types):
                    self._trip_id = txn_header[2]
                if isinstance(txn_header[3], six.string_types):
                    self._referring_path_hash = txn_header[3]
        except Exception:
            pass

    def _generate_response_headers(self, read_length=None):
        nr_headers = []

        # Generate metrics and response headers for inbound cross
        # process web external calls.

        if self.client_cross_process_id is not None:

            # Need to work out queueing time and duration up to this
            # point for inclusion in metrics and response header. If the
            # recording of the transaction had been prematurely stopped
            # via an API call, only return time up until that call was
            # made so it will match what is reported as duration for the
            # transaction.

            if self.queue_start:
                queue_time = self.start_time - self.queue_start
            else:
                queue_time = 0

            if self.end_time:
                duration = self.end_time - self.start_time
            else:
                duration = time.time() - self.start_time

            # Generate the additional response headers which provide
            # information back to the caller. We need to freeze the
            # transaction name before adding to the header.

            self._freeze_path()

            if read_length is None:
                read_length = self._read_length

            read_length = read_length if read_length is not None else -1

            payload = (
                self._settings.cross_process_id,
                self.path,
                queue_time,
                duration,
                read_length,
                self.guid,
                self.record_tt,
            )
            app_data = json_encode(payload)

            nr_headers.append(("X-NewRelic-App-Data", obfuscate(app_data, self._settings.encoding_key)))

        return nr_headers

    def get_response_metadata(self):
        nr_headers = dict(self._generate_response_headers())
        return convert_to_cat_metadata_value(nr_headers)

    def process_request_metadata(self, cat_linking_value):
        try:
            payload = base64_decode(cat_linking_value)
        except:
            # `cat_linking_value` should always be able to be base64_decoded.
            # If this is encountered, the data being sent is corrupt. No
            # exception should be raised.
            return

        nr_headers = json_decode(payload)
        # TODO: All the external CAT APIs really need to
        # be refactored into the transaction class.
        encoded_cross_process_id = nr_headers.get("X-NewRelic-ID")
        encoded_txn_header = nr_headers.get("X-NewRelic-Transaction")
        return self._process_incoming_cat_headers(encoded_cross_process_id, encoded_txn_header)

    def set_transaction_name(self, name, group=None, priority=None):

        # Always perform this operation even if the transaction
        # is not active at the time as will be called from
        # constructor. If path has been frozen do not allow
        # name/group to be overridden. New priority then must be
        # same or greater than existing priority. If no priority
        # always override the existing name/group if not frozen.

        if self._name_priority is None:
            return

        if priority is not None and priority < self._name_priority:
            return

        if priority is not None:
            self._name_priority = priority

        # The name can be a URL for the default case. URLs are
        # supposed to be ASCII but can get a URL with illegal
        # non ASCII characters. As the rule patterns and
        # replacements are Unicode then can get Unicode
        # conversion warnings or errors when URL is converted to
        # Unicode and default encoding is ASCII. Thus need to
        # convert URL to Unicode as Latin-1 explicitly to avoid
        # problems with illegal characters.

        if isinstance(name, bytes):
            name = name.decode("Latin-1")

        # Handle incorrect groupings and leading slashes. This will
        # cause an empty segment which we want to avoid. In that case
        # insert back in Function as the leading segment.

        group = group or "Function"

        if group.startswith("/"):
            group = "Function" + group

        self._group = group
        self._name = name

    def record_exception(self, exc=None, value=None, tb=None, params=None, ignore_errors=None):
        # Deprecation Warning
        warnings.warn(
            ("The record_exception function is deprecated. Please use the new api named notice_error instead."),
            DeprecationWarning,
        )

        self.notice_error(error=(exc, value, tb), attributes=params, ignore=ignore_errors)

    def notice_error(self, error=None, attributes=None, expected=None, ignore=None, status_code=None):
        settings = self._settings

        if not settings:
            return

        if not settings.error_collector.enabled:
            return

        if not settings.collect_errors and not settings.collect_error_events:
            return

        current_span = trace_cache().current_trace()
        if current_span:
            current_span.notice_error(
                error=error,
                attributes=attributes,
                expected=expected,
                ignore=ignore,
                status_code=status_code,
            )

    def _create_error_node(self, settings, fullname, message, expected, custom_params, span_id, tb):
        # Only remember up to limit of what can be caught for a
        # single transaction. This could be trimmed further
        # later if there are already recorded errors and would
        # go over the harvest limit.

        if len(self._errors) >= settings.agent_limits.errors_per_transaction:
            return

        # Check that we have not recorded this exception
        # previously for this transaction due to multiple
        # error traces triggering. This is not going to be
        # exact but the UI hides exceptions of same type
        # anyway. Better that we under count exceptions of
        # same type and message rather than count same one
        # multiple times.

        for error in self._errors:
            if error.type == fullname and error.message == message:
                return

        node = newrelic.core.error_node.ErrorNode(
            timestamp=time.time(),
            type=fullname,
            message=message,
            expected=expected,
            span_id=span_id,
            stack_trace=exception_stack(tb),
            custom_params=custom_params,
            file_name=None,
            line_number=None,
            source=None,
        )

        # TODO Errors are recorded in time order. If
        # there are two exceptions of same type and
        # different message, the UI displays the first
        # one. In the PHP agent it was recording the
        # errors in reverse time order and so the UI
        # displayed the last one. What is the the
        # official order in which they should be sent.

        self._errors.append(node)

    def record_custom_metric(self, name, value):
        self._custom_metrics.record_custom_metric(name, value)

    def record_custom_metrics(self, metrics):
        for name, value in metrics:
            self._custom_metrics.record_custom_metric(name, value)

    def record_custom_event(self, event_type, params):
        settings = self._settings

        if not settings:
            return

        if not settings.custom_insights_events.enabled:
            return

        event = create_custom_event(event_type, params)
        if event:
            self._custom_events.add(event, priority=self.priority)

    def _intern_string(self, value):
        return self._string_cache.setdefault(value, value)

    def _process_node(self, node):
        self._trace_node_count += 1
        node.node_count = self._trace_node_count
        self.total_time += node.exclusive

        if type(node) is newrelic.core.database_node.DatabaseNode:
            settings = self._settings
            if not settings.collect_traces:
                return
            if not settings.slow_sql.enabled and not settings.transaction_tracer.explain_enabled:
                return
            if settings.transaction_tracer.record_sql == "off":
                return
            if node.duration < settings.transaction_tracer.explain_threshold:
                return
            self._slow_sql.append(node)

    def stop_recording(self):
        if not self.enabled:
            return

        if self.stopped:
            return

        if self.end_time:
            return

        self.end_time = time.time()
        self.stopped = True

        if self._utilization_tracker:
            if self._thread_utilization_start:
                if not self._thread_utilization_end:
                    self._thread_utilization_end = self._utilization_tracker.utilization_count()

        self._cpu_user_time_end = os.times()[0]

    def add_custom_parameter(self, name, value):
        if not self._settings:
            return False

        if self._settings.high_security:
            _logger.debug("Cannot add custom parameter in High Security Mode.")
            return False

        if len(self._custom_params) >= MAX_NUM_USER_ATTRIBUTES:
            _logger.debug("Maximum number of custom attributes already added. Dropping attribute: %r=%r", name, value)
            return False

        key, val = process_user_attribute(name, value)

        if key is None:
            return False
        else:
            self._custom_params[key] = val
            return True

    def add_custom_parameters(self, items):
        result = True

        # items is a list of (name, value) tuples.
        for name, value in items:
            result &= self.add_custom_parameter(name, value)

        return result

    def add_framework_info(self, name, version=None):
        if name:
            self._frameworks.add((name, version))

    def dump(self, file):
        """Dumps details about the transaction to the file object."""

        print("Application: %s" % (self.application.name), file=file)
        print("Time Started: %s" % (time.asctime(time.localtime(self.start_time))), file=file)
        print("Thread Id: %r" % (self.thread_id), file=file)
        print("Current Status: %d" % (self._state), file=file)
        print("Recording Enabled: %s" % (self.enabled), file=file)
        print("Ignore Transaction: %s" % (self.ignore_transaction), file=file)
        print("Transaction Dead: %s" % (self._dead), file=file)
        print("Transaction Stopped: %s" % (self.stopped), file=file)
        print("Background Task: %s" % (self.background_task), file=file)
        print("Request URI: %s" % (self._request_uri), file=file)
        print("Transaction Group: %s" % (self._group), file=file)
        print("Transaction Name: %s" % (self._name), file=file)
        print("Name Priority: %r" % (self._name_priority), file=file)
        print("Frozen Path: %s" % (self._frozen_path), file=file)
        print("AutoRUM Disabled: %s" % (self.autorum_disabled), file=file)
        print("Supress Apdex: %s" % (self.suppress_apdex), file=file)


def current_transaction(active_only=True):
    current = trace_cache().current_transaction()
    if active_only:
        if current and (current.ignore_transaction or current.stopped):
            return None
    return current


def set_transaction_name(name, group=None, priority=None):
    transaction = current_transaction()
    if transaction:
        transaction.set_transaction_name(name, group, priority)


def end_of_transaction():
    transaction = current_transaction()
    if transaction:
        transaction.stop_recording()


def set_background_task(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.background_task = flag


def ignore_transaction(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.ignore_transaction = flag


def suppress_apdex_metric(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.suppress_apdex = flag


def capture_request_params(flag=True):
    transaction = current_transaction()
    if transaction and transaction.settings:
        if transaction.settings.high_security:
            _logger.warn("Cannot modify capture_params in High Security Mode.")
        else:
            transaction.capture_params = flag


def add_custom_parameter(key, value):
    transaction = current_transaction()
    if transaction:
        return transaction.add_custom_parameter(key, value)
    else:
        return False


def add_custom_parameters(items):
    transaction = current_transaction()
    if transaction:
        return transaction.add_custom_parameters(items)
    else:
        return False


def add_framework_info(name, version=None):
    transaction = current_transaction()
    if transaction:
        transaction.add_framework_info(name, version)


def get_browser_timing_header():
    transaction = current_transaction()
    if transaction and hasattr(transaction, "browser_timing_header"):
        return transaction.browser_timing_header()
    return ""


def get_browser_timing_footer():
    transaction = current_transaction()
    if transaction and hasattr(transaction, "browser_timing_footer"):
        return transaction.browser_timing_footer()
    return ""


def disable_browser_autorum(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.autorum_disabled = flag


def suppress_transaction_trace(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.suppress_transaction_trace = flag


def record_custom_metric(name, value, application=None):
    if application is None:
        transaction = current_transaction()
        if transaction:
            transaction.record_custom_metric(name, value)
        else:
            _logger.debug(
                "record_custom_metric has been called but no "
                "transaction was running. As a result, the following metric "
                "has not been recorded. Name: %r Value: %r. To correct this "
                "problem, supply an application object as a parameter to this "
                "record_custom_metrics call.",
                name,
                value,
            )
    elif application.enabled:
        application.record_custom_metric(name, value)


def record_custom_metrics(metrics, application=None):
    if application is None:
        transaction = current_transaction()
        if transaction:
            transaction.record_custom_metrics(metrics)
        else:
            _logger.debug(
                "record_custom_metrics has been called but no "
                "transaction was running. As a result, the following metrics "
                "have not been recorded: %r. To correct this problem, "
                "supply an application object as a parameter to this "
                "record_custom_metric call.",
                list(metrics),
            )
    elif application.enabled:
        application.record_custom_metrics(metrics)


def record_custom_event(event_type, params, application=None):
    """Record a custom event.

    Args:
        event_type (str): The type (name) of the custom event.
        params (dict): Attributes to add to the event.
        application (newrelic.api.Application): Application instance.

    """

    if application is None:
        transaction = current_transaction()
        if transaction:
            transaction.record_custom_event(event_type, params)
        else:
            _logger.debug(
                "record_custom_event has been called but no "
                "transaction was running. As a result, the following event "
                "has not been recorded. event_type: %r params: %r. To correct "
                "this problem, supply an application object as a parameter to "
                "this record_custom_event call.",
                event_type,
                params,
            )
    elif application.enabled:
        application.record_custom_event(event_type, params)


def accept_distributed_trace_payload(payload, transport_type="HTTP"):
    transaction = current_transaction()
    if transaction:
        return transaction.accept_distributed_trace_payload(payload, transport_type)
    return False


def accept_distributed_trace_headers(headers, transport_type="HTTP"):
    transaction = current_transaction()
    if transaction:
        return transaction.accept_distributed_trace_headers(headers, transport_type)


def create_distributed_trace_payload():
    transaction = current_transaction()
    if transaction:
        return transaction.create_distributed_trace_payload()


def insert_distributed_trace_headers(headers):
    transaction = current_transaction()
    if transaction:
        return transaction.insert_distributed_trace_headers(headers)


def current_trace_id():
    transaction = current_transaction()
    if transaction:
        return transaction.trace_id


def current_span_id():
    trace = trace_cache().current_trace()
    if trace:
        return trace.guid
