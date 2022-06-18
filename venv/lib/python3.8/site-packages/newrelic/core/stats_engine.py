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

"""The stats engine is what collects the accumulated transactions metrics,
details of errors and slow transactions. There is one instance of the stats
engine per application. This will be cleared upon each successful harvest of
data whereby it is sent to the core application.

"""

import base64
import copy
import logging
import operator
import random
import sys
import time
import warnings
import zlib
from heapq import heapify, heapreplace

import newrelic.packages.six as six
from newrelic.api.settings import STRIP_EXCEPTION_MESSAGE
from newrelic.common.encoding_utils import json_encode
from newrelic.common.object_names import parse_exc_info
from newrelic.common.streaming_utils import StreamBuffer
from newrelic.core.attribute import create_user_attributes, process_user_attribute
from newrelic.core.attribute_filter import DST_ERROR_COLLECTOR
from newrelic.core.config import is_expected_error, should_ignore_error
from newrelic.core.database_utils import explain_plan
from newrelic.core.error_collector import TracedError
from newrelic.core.metric import TimeMetric
from newrelic.core.stack_trace import exception_stack

_logger = logging.getLogger(__name__)

EVENT_HARVEST_METHODS = {
    "analytic_event_data": (
        "reset_transaction_events",
        "reset_synthetics_events",
    ),
    "span_event_data": ("reset_span_events",),
    "custom_event_data": ("reset_custom_events",),
    "error_event_data": ("reset_error_events",),
}


def c2t(count=0, total=0.0, min=0.0, max=0.0, sum_of_squares=0.0):
    return (count, total, total, min, max, sum_of_squares)


class ApdexStats(list):

    """Bucket for accumulating apdex metrics."""

    # Is based on a list of length 6 as all metrics are sent to the core
    # application as that and list as base class means it encodes direct
    # to JSON as we need it. In this case only the first 3 entries are
    # strictly used for the metric. The 4th and 5th entries are set to
    # be the apdex_t value in use at the time.

    def __init__(self, satisfying=0, tolerating=0, frustrating=0, apdex_t=0.0):
        super(ApdexStats, self).__init__([satisfying, tolerating, frustrating, apdex_t, apdex_t, 0])

    satisfying = property(operator.itemgetter(0))
    tolerating = property(operator.itemgetter(1))
    frustrating = property(operator.itemgetter(2))

    def merge_stats(self, other):
        """Merge data from another instance of this object."""

        self[0] += other[0]
        self[1] += other[1]
        self[2] += other[2]

        self[3] = (self[0] or self[1] or self[2]) and min(self[3], other[3]) or other[3]
        self[4] = max(self[4], other[3])

    def merge_apdex_metric(self, metric):
        """Merge data from an apdex metric object."""

        self[0] += metric.satisfying
        self[1] += metric.tolerating
        self[2] += metric.frustrating

        self[3] = (self[0] or self[1] or self[2]) and min(self[3], metric.apdex_t) or metric.apdex_t
        self[4] = max(self[4], metric.apdex_t)


class TimeStats(list):

    """Bucket for accumulating time and value metrics."""

    # Is based on a list of length 6 as all metrics are sent to the core
    # application as that and list as base class means it encodes direct
    # to JSON as we need it.

    def __init__(
        self,
        call_count=0,
        total_call_time=0.0,
        total_exclusive_call_time=0.0,
        min_call_time=0.0,
        max_call_time=0.0,
        sum_of_squares=0.0,
    ):
        if total_exclusive_call_time is None:
            total_exclusive_call_time = total_call_time
        super(TimeStats, self).__init__(
            [call_count, total_call_time, total_exclusive_call_time, min_call_time, max_call_time, sum_of_squares]
        )

    call_count = property(operator.itemgetter(0))
    total_call_time = property(operator.itemgetter(1))
    total_exclusive_call_time = property(operator.itemgetter(2))
    min_call_time = property(operator.itemgetter(3))
    max_call_time = property(operator.itemgetter(4))
    sum_of_squares = property(operator.itemgetter(5))

    def merge_stats(self, other):
        """Merge data from another instance of this object."""

        self[1] += other[1]
        self[2] += other[2]
        self[3] = self[0] and min(self[3], other[3]) or other[3]
        self[4] = max(self[4], other[4])
        self[5] += other[5]

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self[0] += other[0]

    def merge_raw_time_metric(self, duration, exclusive=None):
        """Merge time value."""

        if exclusive is None:
            exclusive = duration

        self[1] += duration
        self[2] += exclusive
        self[3] = self[0] and min(self[3], duration) or duration
        self[4] = max(self[4], duration)
        self[5] += duration**2

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self[0] += 1

    def merge_time_metric(self, metric):
        """Merge data from a time metric object."""

        self.merge_raw_time_metric(metric.duration, metric.exclusive)

    def merge_custom_metric(self, value):
        """Merge data value."""

        self.merge_raw_time_metric(value)


class CountStats(TimeStats):
    def merge_stats(self, other):
        self[0] += other[0]

    def merge_raw_time_metric(self, duration, exclusive=None):
        pass


class CustomMetrics(object):

    """Table for collection a set of value metrics."""

    def __init__(self):
        self.__stats_table = {}

    def __contains__(self, key):
        return key in self.__stats_table

    def record_custom_metric(self, name, value):
        """Record a single value metric, merging the data with any data
        from prior value metrics with the same name.

        """
        if isinstance(value, dict):
            if len(value) == 1 and "count" in value:
                new_stats = CountStats(call_count=value["count"])
            else:
                new_stats = TimeStats(*c2t(**value))
        else:
            new_stats = TimeStats(1, value, value, value, value, value**2)

        stats = self.__stats_table.get(name)
        if stats is None:
            self.__stats_table[name] = new_stats
        else:
            stats.merge_stats(new_stats)

    def metrics(self):
        """Returns an iterator over the set of value metrics. The items
        returned are a tuple consisting of the metric name and accumulated
        stats for the metric.

        """

        return six.iteritems(self.__stats_table)

    def reset_metric_stats(self):
        """Resets the accumulated statistics back to initial state for
        metric data.

        """
        self.__stats_table = {}


class SlowSqlStats(list):
    def __init__(self):
        super(SlowSqlStats, self).__init__([0, 0, 0, 0, None])

    call_count = property(operator.itemgetter(0))
    total_call_time = property(operator.itemgetter(1))
    min_call_time = property(operator.itemgetter(2))
    max_call_time = property(operator.itemgetter(3))
    slow_sql_node = property(operator.itemgetter(4))

    def merge_stats(self, other):
        """Merge data from another instance of this object."""

        self[1] += other[1]
        self[2] = self[0] and min(self[2], other[2]) or other[2]
        self[3] = max(self[3], other[3])

        if self[3] == other[3]:
            self[4] = other[4]

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self[0] += other[0]

    def merge_slow_sql_node(self, node):
        """Merge data from a slow sql node object."""

        duration = node.duration

        self[1] += duration
        self[2] = self[0] and min(self[2], duration) or duration
        self[3] = max(self[3], duration)

        if self[3] == duration:
            self[4] = node

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self[0] += 1


class SampledDataSet(object):
    def __init__(self, capacity=100):
        self.pq = []
        self.heap = False
        self.capacity = capacity
        self.num_seen = 0

        if capacity <= 0:

            def add(*args, **kwargs):
                self.num_seen += 1

            self.add = add

    @property
    def samples(self):
        return (x[-1] for x in self.pq)

    @property
    def num_samples(self):
        return len(self.pq)

    @property
    def sampling_info(self):
        return {"reservoir_size": self.capacity, "events_seen": self.num_seen}

    def __iter__(self):
        return self.samples

    def reset(self):
        self.pq = []
        self.heap = False
        self.num_seen = 0

    def should_sample(self, priority):
        if self.heap:
            # self.pq[0] is always the minimal
            # priority sample in the queue
            if priority > self.pq[0][0]:
                return True
            return False

        # Always sample if under capacity
        return True

    def add(self, sample, priority=None):  # pylint: disable=E0202
        self.num_seen += 1

        if priority is None:
            priority = random.random()  # nosec

        entry = (priority, self.num_seen, sample)
        if self.num_seen == self.capacity:
            self.pq.append(entry)
            self.heap = self.heap or heapify(self.pq) or True
        elif not self.heap:
            self.pq.append(entry)
        else:
            sampled = self.should_sample(priority)
            if not sampled:
                return
            heapreplace(self.pq, entry)

    def merge(self, other_data_set):
        for priority, seen_at, sample in other_data_set.pq:
            self.add(sample, priority)

        # Merge the num_seen from the other_data_set, but take care not to
        # double-count the actual samples of other_data_set since the .add
        # call above will add one to self.num_seen each time
        self.num_seen += other_data_set.num_seen - other_data_set.num_samples


class LimitedDataSet(list):
    def __init__(self, capacity=200):
        super(LimitedDataSet, self).__init__()

        self.capacity = capacity
        self.num_seen = 0

        if capacity <= 0:

            def add(*args, **kwargs):
                self.num_seen += 1

            self.add = add

    @property
    def samples(self):
        return self

    @property
    def num_samples(self):
        return len(self)

    @property
    def sampling_info(self):
        return {"reservoir_size": self.capacity, "events_seen": self.num_seen}

    def should_sample(self):
        return self.num_seen < self.capacity

    def reset(self):
        self.clear()
        self.num_seen = 0

    def add(self, sample):  # pylint: disable=E0202
        if self.should_sample():
            self.append(sample)
        self.num_seen += 1

    def merge(self, other_data_set):
        for sample in other_data_set:
            self.add(sample)

        # Merge the num_seen from the other_data_set, but take care not to
        # double-count the actual samples of other_data_set since the .add
        # call above will add one to self.num_seen each time
        self.num_seen += other_data_set.num_seen - other_data_set.num_samples


class StatsEngine(object):

    """The stats engine object holds the accumulated transactions metrics,
    details of errors and slow transactions. There should be one instance
    of the stats engine per application. This will be cleared upon each
    successful harvest of data whereby it is sent to the core application.
    No data will however be accumulated while there is no associated
    settings object indicating that application has been successfully
    activated and server side settings received.

    All of the accumulated apdex, time and value metrics are mapped to from
    the same stats table. The key is comprised of a tuple (name, scope).
    For an apdex metric the scope is None. Time metrics should always have
    a string as the scope and it can be either empty or not. Value metrics
    technically overlap in same namespace as time metrics as the scope is
    always an empty string. There are however no checks against adding a
    value metric which clashes with an existing time metric or vice versa.
    If that is done then the results will simply be wrong. The name chose
    for a time or value metric should thus be chosen wisely so as not to
    clash.

    Note that there is no locking performed within the stats engine itself.
    It is assumed the holder and user of the instance performs adequate
    external locking to ensure that multiple threads do not try and update
    it at the same time.

    """

    def __init__(self):
        self.__settings = None
        self.__stats_table = {}
        self._transaction_events = SampledDataSet()
        self._error_events = SampledDataSet()
        self._custom_events = SampledDataSet()
        self._span_events = SampledDataSet()
        self._span_stream = None
        self.__sql_stats_table = {}
        self.__slow_transaction = None
        self.__slow_transaction_map = {}
        self.__slow_transaction_old_duration = None
        self.__slow_transaction_dry_harvests = 0
        self.__transaction_errors = []
        self._synthetics_events = LimitedDataSet()
        self.__synthetics_transactions = []

    @property
    def settings(self):
        return self.__settings

    @property
    def stats_table(self):
        return self.__stats_table

    @property
    def transaction_events(self):
        return self._transaction_events

    @property
    def custom_events(self):
        return self._custom_events

    @property
    def span_events(self):
        return self._span_events

    @property
    def span_stream(self):
        return self._span_stream

    @property
    def synthetics_events(self):
        return self._synthetics_events

    @property
    def synthetics_transactions(self):
        return self.__synthetics_transactions

    @property
    def error_events(self):
        return self._error_events

    def metrics_count(self):
        """Returns a count of the number of unique metrics currently
        recorded for apdex, time and value metrics.

        """

        return len(self.__stats_table)

    def record_apdex_metric(self, metric):
        """Record a single apdex metric, merging the data with any data
        from prior apdex metrics with the same name.

        """

        if not self.__settings:
            return

        # Note that because we are using a scope here of an empty string
        # we can potentially clash with an unscoped metric. Using None,
        # although it may help to keep them separate in the agent will
        # not make a difference to the data collector which treats None
        # as an empty string anyway.

        key = (metric.name, "")
        stats = self.__stats_table.get(key)
        if stats is None:
            stats = ApdexStats(apdex_t=metric.apdex_t)
            self.__stats_table[key] = stats
        stats.merge_apdex_metric(metric)

        return key

    def record_apdex_metrics(self, metrics):
        """Record the apdex metrics supplied by the iterable for a
        single transaction, merging the data with any data from prior
        apdex metrics with the same name.

        """

        if not self.__settings:
            return

        for metric in metrics:
            self.record_apdex_metric(metric)

    def record_time_metric(self, metric):
        """Record a single time metric, merging the data with any data
        from prior time metrics with the same name and scope.

        """

        if not self.__settings:
            return

        # Scope is forced to be empty string if None as
        # scope of None is reserved for apdex metrics.

        key = (metric.name, metric.scope or "")
        stats = self.__stats_table.get(key)
        if stats is None:
            stats = TimeStats(
                call_count=1,
                total_call_time=metric.duration,
                total_exclusive_call_time=metric.exclusive,
                min_call_time=metric.duration,
                max_call_time=metric.duration,
                sum_of_squares=metric.duration**2,
            )
            self.__stats_table[key] = stats
        else:
            stats.merge_time_metric(metric)

        return key

    def record_time_metrics(self, metrics):
        """Record the time metrics supplied by the iterable for a single
        transaction, merging the data with any data from prior time
        metrics with the same name and scope.

        """

        if not self.__settings:
            return

        for metric in metrics:
            self.record_time_metric(metric)

    def record_exception(self, exc=None, value=None, tb=None, params=None, ignore_errors=None):
        # Deprecation Warning
        warnings.warn(
            ("The record_exception function is deprecated. Please use the new api named notice_error instead."),
            DeprecationWarning,
        )

        self.notice_error(error=(exc, value, tb), attributes=params, ignore=ignore_errors)

    def notice_error(self, error=None, attributes=None, expected=None, ignore=None, status_code=None):
        attributes = attributes if attributes is not None else {}
        settings = self.__settings

        if not settings:
            return

        error_collector = settings.error_collector

        if not error_collector.enabled:
            return

        if not settings.collect_errors and not settings.collect_error_events:
            return

        # Pull from sys.exc_info if no exception is passed
        if not error or None in error:
            error = sys.exc_info()

            # If no exception to report, exit
            if not error or None in error:
                return

        exc, value, tb = error

        if getattr(value, "_nr_ignored", None):
            return

        module, name, fullnames, message = parse_exc_info(error)
        fullname = fullnames[0]

        # Check to see if we need to strip the message before recording it.

        if settings.strip_exception_messages.enabled and fullname not in settings.strip_exception_messages.whitelist:
            message = STRIP_EXCEPTION_MESSAGE

        # Where expected or ignore are a callable they should return a
        # tri-state variable with the following behavior.
        #
        #   True - Ignore the error.
        #   False- Record the error.
        #   None - Use the default rules.

        # Precedence:
        # 1. function parameter override as bool
        # 2. function parameter callable
        # 3. function parameter iterable of class names
        # 4. default rule matching from settings

        should_ignore = None
        is_expected = None

        # Check against ignore rules
        # Boolean parameter (True/False only, not None)
        if isinstance(ignore, bool):
            should_ignore = ignore
            if should_ignore:
                value._nr_ignored = True
                return

        # Callable parameter
        if should_ignore is None and callable(ignore):
            should_ignore = ignore(exc, value, tb)
            if should_ignore:
                value._nr_ignored = True
                return

        # List of class names
        if should_ignore is None and ignore is not None and not callable(ignore):
            # Do not set should_ignore to False
            # This should cascade into default settings rule matching
            for name in fullnames:
                if name in ignore:
                    value._nr_ignored = True
                    return

        # Default rule matching
        if should_ignore is None:
            should_ignore = should_ignore_error(error, status_code=status_code, settings=settings)
            if should_ignore:
                value._nr_ignored = True
                return

        # Check against expected rules
        # Boolean parameter (True/False only, not None)
        if isinstance(expected, bool):
            is_expected = expected

        # Callable parameter
        if is_expected is None and callable(expected):
            is_expected = expected(exc, value, tb)

        # List of class names
        if is_expected is None and expected is not None and not callable(expected):
            # Do not set is_expected to False
            # This should cascade into default settings rule matching
            for name in fullnames:
                if name in expected:
                    is_expected = True

        # Default rule matching
        if is_expected is None:
            is_expected = is_expected_error(error, status_code=status_code, settings=settings)

        # Only add attributes if High Security Mode is off.

        if settings.high_security:
            if attributes:
                _logger.debug("Cannot add custom parameters in High Security Mode.")
            user_attributes = []
        else:
            custom_attributes = {}

            try:
                for k, v in attributes.items():
                    name, val = process_user_attribute(k, v)
                    if name:
                        custom_attributes[name] = val
            except Exception:
                _logger.debug(
                    "Parameters failed to validate for unknown "
                    "reason. Dropping parameters for error: %r. Check "
                    "traceback for clues.",
                    fullname,
                    exc_info=True,
                )
                custom_attributes = {}

            user_attributes = create_user_attributes(custom_attributes, settings.attribute_filter)

        # Record the exception details.

        attributes = {}

        attributes["stack_trace"] = exception_stack(tb)

        # filter custom error specific attributes using attribute filter (user)
        attributes["userAttributes"] = {}
        for attr in user_attributes:
            if attr.destinations & DST_ERROR_COLLECTOR:
                attributes["userAttributes"][attr.name] = attr.value

        # pass expected attribute in to ensure we capture overrides
        attributes["intrinsics"] = {
            "error.expected": is_expected,
        }

        error_details = TracedError(
            start_time=time.time(), path="Exception", message=message, type=fullname, parameters=attributes
        )

        # Save this error as a trace and an event.

        if error_collector.capture_events and settings.collect_error_events:
            event = self._error_event(error_details)
            self._error_events.add(event)

        if settings.collect_errors and (len(self.__transaction_errors) < settings.agent_limits.errors_per_harvest):
            self.__transaction_errors.append(error_details)

        # Regardless of whether we record the trace or the event we still
        # want to increment the metric Errors/all unless the error was marked
        # as expected
        if is_expected:
            self.record_time_metric(TimeMetric(name="ErrorsExpected/all", scope="", duration=0.0, exclusive=None))
        else:
            self.record_time_metric(TimeMetric(name="Errors/all", scope="", duration=0.0, exclusive=None))

    def _error_event(self, error):

        # This method is for recording error events outside of transactions,
        # don't let the poorly named 'type' attribute fool you.

        error.parameters["intrinsics"].update(
            {
                "type": "TransactionError",
                "error.class": error.type,
                "error.message": error.message,
                "timestamp": int(1000.0 * error.start_time),
                "transactionName": None,
            }
        )

        # Leave agent attributes field blank since not a transaction

        error_event = [error.parameters["intrinsics"], error.parameters["userAttributes"], {}]

        return error_event

    def record_custom_event(self, event):

        settings = self.__settings

        if not settings:
            return

        if settings.collect_custom_events and settings.custom_insights_events.enabled:
            self._custom_events.add(event)

    def record_custom_metric(self, name, value):
        """Record a single value metric, merging the data with any data
        from prior value metrics with the same name.

        """
        key = (name, "")

        if isinstance(value, dict):
            if len(value) == 1 and "count" in value:
                new_stats = CountStats(call_count=value["count"])
            else:
                new_stats = TimeStats(*c2t(**value))
        else:
            new_stats = TimeStats(1, value, value, value, value, value**2)

        stats = self.__stats_table.get(key)
        if stats is None:
            self.__stats_table[key] = new_stats
        else:
            stats.merge_stats(new_stats)

        return key

    def record_custom_metrics(self, metrics):
        """Record the value metrics supplied by the iterable, merging
        the data with any data from prior value metrics with the same
        name.

        """

        if not self.__settings:
            return

        for name, value in metrics:
            self.record_custom_metric(name, value)

    def record_slow_sql_node(self, node):
        """Record a single sql metric, merging the data with any data
        from prior sql metrics for the same sql key.

        """

        if not self.__settings:
            return

        key = node.identifier
        stats = self.__sql_stats_table.get(key)
        if stats is None:
            # Only record slow SQL if not already over the limit on
            # how many can be collected in the harvest period.

            settings = self.__settings
            maximum = settings.agent_limits.slow_sql_data
            if len(self.__sql_stats_table) < maximum:
                stats = SlowSqlStats()
                self.__sql_stats_table[key] = stats

        if stats:
            stats.merge_slow_sql_node(node)

        return key

    def _update_slow_transaction(self, transaction):
        """Check if transaction is the slowest transaction and update
        accordingly.
        """

        slowest = 0
        name = transaction.path

        if self.__slow_transaction:
            slowest = self.__slow_transaction.duration
        if name in self.__slow_transaction_map:
            slowest = max(self.__slow_transaction_map[name], slowest)

        if transaction.duration > slowest:
            # We are going to replace the prior slow transaction.
            # We need to be a bit tricky here. If we are overriding
            # an existing slow transaction for a different name,
            # then we need to restore in the transaction map what
            # the previous slowest duration was for that, or remove
            # it if there wasn't one. This is so we do not incorrectly
            # suppress it given that it was never actually reported
            # as the slowest transaction.

            if self.__slow_transaction:
                if self.__slow_transaction.path != name:
                    if self.__slow_transaction_old_duration:
                        self.__slow_transaction_map[self.__slow_transaction.path] = self.__slow_transaction_old_duration
                    else:
                        del self.__slow_transaction_map[self.__slow_transaction.path]

            if name in self.__slow_transaction_map:
                self.__slow_transaction_old_duration = self.__slow_transaction_map[name]
            else:
                self.__slow_transaction_old_duration = None

            self.__slow_transaction = transaction
            self.__slow_transaction_map[name] = transaction.duration

    def _update_synthetics_transaction(self, transaction):
        """Check if transaction is a synthetics trace and save it to
        __synthetics_transactions.
        """

        settings = self.__settings

        if not transaction.synthetics_resource_id:
            return

        maximum = settings.agent_limits.synthetics_transactions
        if len(self.__synthetics_transactions) < maximum:
            self.__synthetics_transactions.append(transaction)

    def record_transaction(self, transaction):
        """Record any apdex and time metrics for the transaction as
        well as any errors which occurred for the transaction. If the
        transaction qualifies to become the slow transaction remember
        it for later.

        """

        if not self.__settings:
            return

        settings = self.__settings

        # Record the apdex, value and time metrics generated from the
        # transaction. Whether time metrics are reported as distinct
        # metrics or into a rollup is in part controlled via settings
        # for minimum number of unique metrics to be reported and thence
        # whether over a time threshold calculated as percentage of
        # overall request time, up to a maximum number of unique
        # metrics. This is intended to limit how many metrics are
        # reported for each transaction and try and cut down on an
        # explosion of unique metric names. The limits and thresholds
        # are applied after the metrics are reverse sorted based on
        # exclusive times for each metric. This ensures that the metrics
        # with greatest exclusive time are retained over those with
        # lesser time. Such metrics get reported into the performance
        # breakdown tab for specific web transactions.

        self.record_apdex_metrics(transaction.apdex_metrics(self))

        self.merge_custom_metrics(transaction.custom_metrics.metrics())

        self.record_time_metrics(transaction.time_metrics(self))

        # Capture any errors if error collection is enabled.
        # Only retain maximum number allowed per harvest.

        error_collector = settings.error_collector

        if (
            error_collector.enabled
            and settings.collect_errors
            and len(self.__transaction_errors) < settings.agent_limits.errors_per_harvest
        ):
            self.__transaction_errors.extend(transaction.error_details())

            self.__transaction_errors = self.__transaction_errors[: settings.agent_limits.errors_per_harvest]

        if error_collector.capture_events and error_collector.enabled and settings.collect_error_events:
            events = transaction.error_events(self.__stats_table)
            for event in events:
                self._error_events.add(event, priority=transaction.priority)

        # Capture any sql traces if transaction tracer enabled.

        if settings.slow_sql.enabled and settings.collect_traces:
            for node in transaction.slow_sql_nodes(self):
                self.record_slow_sql_node(node)

        # Remember as slowest transaction if transaction tracer
        # is enabled, it is over the threshold and slower than
        # any existing transaction seen for this period and in
        # the historical snapshot of slow transactions, plus
        # recording of transaction trace for this transaction
        # has not been suppressed.

        transaction_tracer = settings.transaction_tracer

        if not transaction.suppress_transaction_trace and transaction_tracer.enabled and settings.collect_traces:

            # Transactions saved for Synthetics transactions
            # do not depend on the transaction threshold.

            self._update_synthetics_transaction(transaction)

            threshold = transaction_tracer.transaction_threshold

            if threshold is None:
                threshold = transaction.apdex_t * 4

            if transaction.duration >= threshold:
                self._update_slow_transaction(transaction)

        # Create the transaction event and add it to the
        # appropriate "bucket." Synthetic requests are saved in one,
        # while transactions from regular requests are saved in another.

        if transaction.synthetics_resource_id:
            event = transaction.transaction_event(self.__stats_table)
            self._synthetics_events.add(event)

        elif settings.collect_analytics_events and settings.transaction_events.enabled:

            event = transaction.transaction_event(self.__stats_table)
            self._transaction_events.add(event, priority=transaction.priority)

        # Merge in custom events

        if settings.collect_custom_events and settings.custom_insights_events.enabled:
            self.custom_events.merge(transaction.custom_events)

        # Merge in span events

        if settings.distributed_tracing.enabled and settings.span_events.enabled and settings.collect_span_events:
            if settings.infinite_tracing.enabled:
                for event in transaction.span_protos(settings):
                    self._span_stream.put(event)
            elif transaction.sampled:
                for event in transaction.span_events(self.__settings):
                    self._span_events.add(event, priority=transaction.priority)

    def metric_data(self, normalizer=None):
        """Returns a list containing the low level metric data for
        sending to the core application pertaining to the reporting
        period. This consists of tuple pairs where first is dictionary
        with name and scope keys with corresponding values, or integer
        identifier if metric had an entry in dictionary mapping metric
        (name, scope) as supplied from core application. The second is
        the list of accumulated metric data, the list always being of
        length 6.

        """

        if not self.__settings:
            return []

        result = []
        normalized_stats = {}

        # Metric Renaming and Re-Aggregation. After applying the metric
        # renaming rules, the metrics are re-aggregated to collapse the
        # metrics with same names after the renaming.

        if self.__settings.debug.log_raw_metric_data:
            _logger.info(
                "Raw metric data for harvest of %r is %r.",
                self.__settings.app_name,
                list(six.iteritems(self.__stats_table)),
            )

        if normalizer is not None:
            for key, value in six.iteritems(self.__stats_table):
                key = (normalizer(key[0])[0], key[1])
                stats = normalized_stats.get(key)
                if stats is None:
                    normalized_stats[key] = copy.copy(value)
                else:
                    stats.merge_stats(value)
        else:
            normalized_stats = self.__stats_table

        if self.__settings.debug.log_normalized_metric_data:
            _logger.info(
                "Normalized metric data for harvest of %r is %r.",
                self.__settings.app_name,
                list(six.iteritems(normalized_stats)),
            )

        for key, value in six.iteritems(normalized_stats):
            key = dict(name=key[0], scope=key[1])
            result.append((key, value))

        return result

    def metric_data_count(self):
        """Returns a count of the number of unique metrics."""

        if not self.__settings:
            return 0

        return len(self.__stats_table)

    def error_data(self):
        """Returns a to a list containing any errors collected during
        the reporting period.

        """

        if not self.__settings:
            return []

        return self.__transaction_errors

    def slow_sql_data(self, connections):

        _logger.debug("Generating slow SQL data.")

        if not self.__settings:
            return []

        if not self.__sql_stats_table:
            return []

        if not self.__settings.slow_sql.enabled:
            return []

        maximum = self.__settings.agent_limits.slow_sql_data

        slow_sql_nodes = sorted(six.itervalues(self.__sql_stats_table), key=lambda x: x.max_call_time)[-maximum:]

        result = []

        for stats_node in slow_sql_nodes:

            slow_sql_node = stats_node.slow_sql_node

            params = slow_sql_node.params or {}

            if slow_sql_node.stack_trace:
                params["backtrace"] = slow_sql_node.stack_trace

            explain_plan_data = explain_plan(
                connections,
                slow_sql_node.statement,
                slow_sql_node.connect_params,
                slow_sql_node.cursor_params,
                slow_sql_node.sql_parameters,
                slow_sql_node.execute_params,
                slow_sql_node.sql_format,
            )

            if explain_plan_data:
                params["explain_plan"] = explain_plan_data

            # Only send datastore instance params if not empty.

            if slow_sql_node.host:
                params["host"] = slow_sql_node.host

            if slow_sql_node.port_path_or_id:
                params["port_path_or_id"] = slow_sql_node.port_path_or_id

            if slow_sql_node.database_name:
                params["database_name"] = slow_sql_node.database_name

            json_data = json_encode(params)

            level = self.__settings.agent_limits.data_compression_level
            level = level or zlib.Z_DEFAULT_COMPRESSION

            params_data = base64.standard_b64encode(zlib.compress(six.b(json_data), level))

            if six.PY3:
                params_data = params_data.decode("Latin-1")

            # Limit the length of any SQL that is reported back.

            limit = self.__settings.agent_limits.sql_query_length_maximum

            sql = slow_sql_node.formatted[:limit]

            data = [
                slow_sql_node.path,
                slow_sql_node.request_uri,
                slow_sql_node.identifier,
                sql,
                slow_sql_node.metric,
                stats_node.call_count,
                stats_node.total_call_time * 1000,
                stats_node.min_call_time * 1000,
                stats_node.max_call_time * 1000,
                params_data,
            ]

            result.append(data)

        return result

    def transaction_trace_data(self, connections):
        """Returns a list of slow transaction data collected
        during the reporting period.

        """

        _logger.debug("Generating transaction trace data.")

        if not self.__settings:
            return []

        # Create a set 'traces' that is a union of slow transaction,
        # and Synthetics transactions. This ensures we don't send
        # duplicates of a transaction.

        traces = set()
        if self.__slow_transaction:
            traces.add(self.__slow_transaction)
        traces.update(self.__synthetics_transactions)

        # Return an empty list if no transactions were captured.

        if not traces:
            return []

        # We want to limit the number of explain plans we do across
        # these. So work out what were the slowest and tag them.
        # Later the explain plan will only be run on those which are
        # tagged.

        agent_limits = self.__settings.agent_limits
        explain_plan_limit = agent_limits.sql_explain_plans_per_harvest
        maximum_nodes = agent_limits.transaction_traces_nodes

        database_nodes = []

        if explain_plan_limit != 0:
            for trace in traces:
                for node in trace.slow_sql:
                    # Make sure we clear any flag for explain plans on
                    # the nodes in case a transaction trace was merged
                    # in from previous harvest period.

                    node.generate_explain_plan = False

                    # Node should be excluded if not for an operation
                    # that we can't do an explain plan on. Also should
                    # not be one which would not be included in the
                    # transaction trace because limit was reached.

                    if (
                        node.node_count < maximum_nodes
                        and node.connect_params
                        and node.statement.operation in node.statement.database.explain_stmts
                    ):
                        database_nodes.append(node)

            database_nodes = sorted(database_nodes, key=lambda x: x.duration)[-explain_plan_limit:]

            for node in database_nodes:
                node.generate_explain_plan = True

        else:
            for trace in traces:
                for node in trace.slow_sql:
                    node.generate_explain_plan = True
                    database_nodes.append(node)

        # Now generate the transaction traces. We need to cap the
        # number of nodes capture to the specified limit.

        trace_data = []

        for trace in traces:
            transaction_trace = trace.transaction_trace(self, maximum_nodes, connections)

            data = [transaction_trace, list(trace.string_table.values())]

            if self.__settings.debug.log_transaction_trace_payload:
                _logger.debug("Encoding slow transaction data where payload=%r.", data)

            json_data = json_encode(data)

            level = self.__settings.agent_limits.data_compression_level
            level = level or zlib.Z_DEFAULT_COMPRESSION

            zlib_data = zlib.compress(six.b(json_data), level)

            pack_data = base64.standard_b64encode(zlib_data)

            if six.PY3:
                pack_data = pack_data.decode("Latin-1")

            root = transaction_trace.root

            force_persist = bool(trace.record_tt)  # Check if exists

            if trace.include_transaction_trace_request_uri:
                request_uri = trace.request_uri
            else:
                request_uri = None

            trace_data.append(
                [
                    transaction_trace.start_time,
                    root.end_time - root.start_time,
                    trace.path,
                    request_uri,
                    pack_data,
                    trace.guid,
                    None,
                    force_persist,
                    None,
                    trace.synthetics_resource_id,
                ]
            )

        return trace_data

    def slow_transaction_data(self):
        """Returns a list containing any slow transaction data collected
        during the reporting period.

        NOTE Currently only the slowest transaction for the reporting
        period is retained.

        """

        # XXX This method no longer appears to be used. Being replaced
        # by the transaction_trace_data() method.

        if not self.__settings:
            return []

        if not self.__slow_transaction:
            return []

        maximum = self.__settings.agent_limits.transaction_traces_nodes

        transaction_trace = self.__slow_transaction.transaction_trace(self, maximum)

        data = [transaction_trace, list(self.__slow_transaction.string_table.values())]

        if self.__settings.debug.log_transaction_trace_payload:
            _logger.debug("Encoding slow transaction data where payload=%r.", data)

        json_data = json_encode(data)

        level = self.__settings.agent_limits.data_compression_level
        level = level or zlib.Z_DEFAULT_COMPRESSION

        zlib_data = zlib.compress(six.b(json_data), level)

        pack_data = base64.standard_b64encode(zlib_data)

        if six.PY3:
            pack_data = pack_data.decode("Latin-1")

        root = transaction_trace.root

        trace_data = [
            [
                root.start_time,
                root.end_time - root.start_time,
                self.__slow_transaction.path,
                self.__slow_transaction.request_uri,
                pack_data,
            ]
        ]

        return trace_data

    def reset_stats(self, settings, reset_stream=False):
        """Resets the accumulated statistics back to initial state and
        associates the application settings object with the stats
        engine. This should be called when application is first
        activated and combined application settings incorporating server
        side settings are available. Would also be called on any forced
        restart of agent or a reconnection due to loss of connection.

        """

        self.__settings = settings
        self.__stats_table = {}
        self.__sql_stats_table = {}
        self.__slow_transaction = None
        self.__slow_transaction_map = {}
        self.__slow_transaction_old_duration = None
        self.__transaction_errors = []
        self.__synthetics_transactions = []

        self.reset_transaction_events()
        self.reset_error_events()
        self.reset_custom_events()
        self.reset_span_events()
        self.reset_synthetics_events()
        # streams are never reset after instantiation
        if reset_stream:
            self._span_stream = StreamBuffer(settings.infinite_tracing.span_queue_size)

    def reset_metric_stats(self):
        """Resets the accumulated statistics back to initial state for
        metric data.

        """

        self.__stats_table = {}

    def reset_transaction_events(self):
        """Resets the accumulated statistics back to initial state for
        sample analytics data.

        """

        if self.__settings is not None:
            self._transaction_events = SampledDataSet(
                self.__settings.event_harvest_config.harvest_limits.analytic_event_data
            )
        else:
            self._transaction_events = SampledDataSet()

    def reset_error_events(self):
        if self.__settings is not None:
            self._error_events = SampledDataSet(self.__settings.event_harvest_config.harvest_limits.error_event_data)
        else:
            self._error_events = SampledDataSet()

    def reset_custom_events(self):
        if self.__settings is not None:
            self._custom_events = SampledDataSet(self.__settings.event_harvest_config.harvest_limits.custom_event_data)
        else:
            self._custom_events = SampledDataSet()

    def reset_span_events(self):
        if self.__settings is not None:
            self._span_events = SampledDataSet(self.__settings.event_harvest_config.harvest_limits.span_event_data)
        else:
            self._span_events = SampledDataSet()

    def reset_synthetics_events(self):
        """Resets the accumulated statistics back to initial state for
        Synthetics events data.

        """
        if self.__settings is not None:
            self._synthetics_events = LimitedDataSet(self.__settings.agent_limits.synthetics_events)
        else:
            self._synthetics_events = LimitedDataSet()

    def reset_non_event_types(self):
        # The slow transaction map is retained but we need to
        # perform some housework on each harvest snapshot. What
        # we do is add the slow transaction to the map of
        # transactions and if we reach the threshold for maximum
        # number we clear the table. Also clear the table if
        # have number of harvests where no slow transaction was
        # collected.
        if self.__settings is None:
            self.__slow_transaction_dry_harvests = 0
            self.__slow_transaction_map = {}
            self.__slow_transaction_old_duration = None

        elif self.__slow_transaction is None:
            self.__slow_transaction_dry_harvests += 1
            agent_limits = self.__settings.agent_limits
            dry_harvests = agent_limits.slow_transaction_dry_harvests
            if self.__slow_transaction_dry_harvests >= dry_harvests:
                self.__slow_transaction_dry_harvests = 0
                self.__slow_transaction_map = {}
                self.__slow_transaction_old_duration = None

        else:
            self.__slow_transaction_dry_harvests = 0
            name = self.__slow_transaction.path
            duration = self.__slow_transaction.duration
            self.__slow_transaction_map[name] = duration

            top_n = self.__settings.transaction_tracer.top_n
            if len(self.__slow_transaction_map) >= top_n:
                self.__slow_transaction_map = {}
                self.__slow_transaction_old_duration = None

        self.__slow_transaction = None
        self.__synthetics_transactions = []
        self.__sql_stats_table = {}
        self.__stats_table = {}
        self.__transaction_errors = []

    def harvest_snapshot(self, flexible=False):
        """Creates a snapshot of the accumulated statistics, error
        details and slow transaction and returns it. This is a shallow
        copy, only copying the top level objects. The originals are then
        reset back to being empty, with the exception of the dictionary
        mapping metric (name, scope) to the integer identifiers received
        from the core application. The latter is retained as should
        carry forward to subsequent runs. This method would be called
        to snapshot the data when doing the harvest.

        """
        snapshot = self._snapshot()

        # Data types only appear in one place, so during a snapshot it must be
        # represented in either the snapshot or in the current stats object.
        #
        #   If we're in flexible harvest, the goal is to have everything in the
        #   whitelist appear in the snapshot. This means, we must remove the
        #   whitelist data types from the current stats object.
        #
        #   If we're not in flexible harvest, everything excluded from the
        #   whitelist appears in the snapshot and is removed from the current
        #   stats object.
        if flexible:
            whitelist_stats, other_stats = self, snapshot
            snapshot.reset_non_event_types()
        else:
            whitelist_stats, other_stats = snapshot, self
            self.reset_non_event_types()

        event_harvest_whitelist = self.__settings.event_harvest_config.whitelist

        # Iterate through harvest types. If they are in the list of types to
        # harvest reset them on stats_engine otherwise remove them from the
        # snapshot.
        for nr_method, stats_methods in EVENT_HARVEST_METHODS.items():
            for stats_method in stats_methods:
                if nr_method in event_harvest_whitelist:
                    reset = getattr(whitelist_stats, stats_method)
                else:
                    reset = getattr(other_stats, stats_method)

                reset()

        return snapshot

    def create_workarea(self):
        """Creates and returns a new empty stats engine object. This would
        be used to distill stats from a single web transaction before then
        merging it back into the parent under a thread lock.

        """

        stats = copy.copy(self)
        stats.reset_stats(self.__settings)

        return stats

    def merge(self, snapshot):
        """Merges data from a single transaction. Snapshot is an instance of
        StatsEngine that contains stats for the single transaction.
        """

        if not self.__settings:
            return

        self.merge_metric_stats(snapshot)
        self._merge_transaction_events(snapshot)
        self._merge_synthetics_events(snapshot)
        self._merge_error_events(snapshot)
        self._merge_error_traces(snapshot)
        self._merge_custom_events(snapshot)
        self._merge_span_events(snapshot)
        self._merge_sql(snapshot)
        self._merge_traces(snapshot)

    def rollback(self, snapshot):
        """Performs a "rollback" merge after a failed harvest. Snapshot is a
        copy of the main StatsEngine data that we attempted to harvest, but
        failed. Not all types of data get merged during a rollback.
        """

        if not self.__settings:
            return

        _logger.debug(
            "Performing rollback of data into "
            "subsequent harvest period. Metric data and transaction events"
            "will be preserved and rolled into next harvest"
        )

        self.merge_metric_stats(snapshot)
        self._merge_transaction_events(snapshot, rollback=True)
        self._merge_synthetics_events(snapshot, rollback=True)
        self._merge_error_events(snapshot)
        self._merge_custom_events(snapshot, rollback=True)
        self._merge_span_events(snapshot, rollback=True)

    def merge_metric_stats(self, snapshot):
        """Merges metric data from a snapshot. This is used both when merging
        data from a single transaction into the main stats engine, and for
        performing a rollback merge. In either case, the merge is done the
        exact same way.
        """

        if not self.__settings:
            return

        for key, other in six.iteritems(snapshot.__stats_table):
            stats = self.__stats_table.get(key)
            if not stats:
                self.__stats_table[key] = other
            else:
                stats.merge_stats(other)

    def _merge_transaction_events(self, snapshot, rollback=False):

        # Merge in transaction events. In the normal case snapshot is a
        # StatsEngine from a single transaction, and should only have one
        # event. Just to avoid issues, if there is more than one, don't merge.

        # If this is a rollback, snapshot is a copy of a previous main
        # StatsEngine, and self is still the current main StatsEngine. Then
        # we are merging multiple events, but still using the reservoir
        # sampling that gives equal probability for keeping all events
        events = snapshot.transaction_events
        if not events:
            return
        if rollback:
            self._transaction_events.merge(events)
        else:
            if events.num_samples == 1:
                self._transaction_events.merge(events)

    def _merge_synthetics_events(self, snapshot, rollback=False):

        # Merge Synthetic analytic events, appending to the list
        # that contains events from previous transactions. In the normal
        # case snapshot is a StatsEngine from a single transaction, and should
        # only have one event. Cap this list at a maximum, so that newer events
        # over the limit will be thrown out.

        # If this is a rollback, snapshot is a copy of a previous main
        # StatsEngine, and self is still the current main StatsEngine,
        # Thus, the events already existing in this object will be newer than
        # those in snapshot, and we favor the newer events.
        events = snapshot.synthetics_events
        if not events:
            return
        self._synthetics_events.merge(events)

    def _merge_error_events(self, snapshot):

        # Merge in error events. Since we are using reservoir sampling that
        # gives equal probability to keeping each event, merge is the same as
        # rollback. There may be multiple error events per transaction.
        events = snapshot.error_events
        if not events:
            return
        self._error_events.merge(events)

    def _merge_custom_events(self, snapshot, rollback=False):
        events = snapshot.custom_events
        if not events:
            return
        self._custom_events.merge(events)

    def _merge_span_events(self, snapshot, rollback=False):
        events = snapshot.span_events
        if not events:
            return
        self._span_events.merge(events)

    def _merge_error_traces(self, snapshot):

        # Append snapshot error details at end to maintain time
        # based order and then trim at maximum to be kept. snapshot will
        # always have newer data.

        maximum = self.__settings.agent_limits.errors_per_harvest
        self.__transaction_errors.extend(snapshot.__transaction_errors)
        self.__transaction_errors = self.__transaction_errors[:maximum]

    def _merge_sql(self, snapshot):

        # Add sql traces to the set of existing entries. If over
        # the limit of how many to collect, only merge in if already
        # seen the specific SQL.

        for key, slow_sql_stats in six.iteritems(snapshot.__sql_stats_table):
            stats = self.__sql_stats_table.get(key)
            if not stats:
                maximum = self.__settings.agent_limits.slow_sql_data
                if len(self.__sql_stats_table) < maximum:
                    self.__sql_stats_table[key] = copy.copy(slow_sql_stats)
            else:
                stats.merge_stats(slow_sql_stats)

    def _merge_traces(self, snapshot):

        # Limit number of Synthetics transactions

        maximum = self.__settings.agent_limits.synthetics_transactions
        self.__synthetics_transactions.extend(snapshot.__synthetics_transactions)
        synthetics_slice = self.__synthetics_transactions[:maximum]
        self.__synthetics_transactions = synthetics_slice

        transaction = snapshot.__slow_transaction

        if transaction:
            # Restore original slow transaction if slower than any newer slow
            # transaction.

            self._update_slow_transaction(transaction)

    def merge_custom_metrics(self, metrics):
        """Merges in a set of custom metrics. The metrics should be
        provide as an iterable where each item is a tuple of the metric
        name and the accumulated stats for the metric.

        """

        if not self.__settings:
            return

        for name, other in metrics:
            key = (name, "")
            stats = self.__stats_table.get(key)
            if not stats:
                self.__stats_table[key] = other
            else:
                stats.merge_stats(other)

    def _snapshot(self):
        copy = object.__new__(StatsEngineSnapshot)
        copy.__dict__.update(self.__dict__)
        return copy


class StatsEngineSnapshot(StatsEngine):
    def reset_transaction_events(self):
        self._transaction_events = None

    def reset_custom_events(self):
        self._custom_events = None

    def reset_span_events(self):
        self._span_events = None

    def reset_synthetics_events(self):
        self._synthetics_events = None

    def reset_error_events(self):
        self._error_events = None
