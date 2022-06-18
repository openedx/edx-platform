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

import logging
import random
import sys
import time
import traceback
import warnings

from newrelic.api.settings import STRIP_EXCEPTION_MESSAGE
from newrelic.common.object_names import parse_exc_info
from newrelic.core.attribute import MAX_NUM_USER_ATTRIBUTES, process_user_attribute
from newrelic.core.config import is_expected_error, should_ignore_error
from newrelic.core.trace_cache import trace_cache

_logger = logging.getLogger(__name__)


class TimeTrace(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.root = None
        self.child_count = 0
        self.children = []
        self.start_time = 0.0
        self.end_time = 0.0
        self.duration = 0.0
        self.exclusive = 0.0
        self.thread_id = None
        self.activated = False
        self.exited = False
        self.is_async = False
        self.has_async_children = False
        self.min_child_start_time = float("inf")
        self.exc_data = (None, None, None)
        self.should_record_segment_params = False
        # 16-digit random hex. Padded with zeros in the front.
        self.guid = "%016x" % random.getrandbits(64)
        self.agent_attributes = {}
        self.user_attributes = {}

    @property
    def transaction(self):
        return self.root and self.root.transaction

    @property
    def settings(self):
        transaction = self.transaction
        return transaction and transaction.settings

    def _is_leaf(self):
        return self.child_count == len(self.children)

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (self.__class__.__name__, id(self), dict(name=getattr(self, "name", None)))

    def __enter__(self):
        self.parent = parent = self.parent or current_trace()
        if not parent:
            return self

        # The parent may be exited if the stack is not consistent. This
        # can occur when using ensure_future to schedule coroutines
        # instead of using async/await keywords. In those cases, we
        # must not trace.
        #
        # Don't do any tracing if parent is designated
        # as a terminal node.
        if parent.exited or parent.terminal_node():
            self.parent = None
            return parent

        transaction = parent.root.transaction

        # Don't do further tracing of transaction if
        # it has been explicitly stopped.
        if transaction.stopped or not transaction.enabled:
            self.parent = None
            return self

        parent.increment_child_count()

        self.root = parent.root
        self.should_record_segment_params = transaction.should_record_segment_params

        # Record start time.

        self.start_time = time.time()

        cache = trace_cache()
        self.thread_id = cache.current_thread_id()

        # Push ourselves as the current node and store parent.
        try:
            cache.save_trace(self)
        except:
            self.parent = None
            raise

        self.activated = True

        return self

    def __exit__(self, exc, value, tb):
        if not self.parent:
            return

        # Check for violation of context manager protocol where
        # __exit__() is called before __enter__().

        if not self.activated:
            _logger.error(
                "Runtime instrumentation error. The __exit__() "
                "method of %r was called prior to __enter__() being "
                "called. Report this issue to New Relic support.\n%s",
                self,
                "".join(traceback.format_stack()[:-1]),
            )

            return

        transaction = self.root.transaction

        # If the transaction has gone out of scope (recorded), there's not much
        # we can do at this point.
        if not transaction:
            return

        # If recording of time for transaction has already been
        # stopped, then that time has to be used.

        if transaction.stopped:
            self.end_time = transaction.end_time
        else:
            self.end_time = time.time()

        # Ensure end time is greater. Should be unless the
        # system clock has been updated.

        if self.end_time < self.start_time:
            self.end_time = self.start_time

        # Calculate duration and exclusive time. Up till now the
        # exclusive time value had been used to accumulate
        # duration from child nodes as negative value, so just
        # add duration to that to get our own exclusive time.

        self.duration = self.end_time - self.start_time

        self.exclusive += self.duration

        # Set negative values to 0
        self.exclusive = max(self.exclusive, 0)

        self.exited = True

        self.exc_data = (exc, value, tb)

        # in all cases except async, the children will have exited
        # so this will create the node

        if self._ready_to_complete():
            self._complete_trace()
        else:
            # Since we're exited we can't possibly schedule more children but
            # we may have children still running if we're async
            trace_cache().pop_current(self)

    def add_custom_attribute(self, key, value):
        settings = self.settings
        if not settings:
            return

        if settings.high_security:
            _logger.debug("Cannot add custom parameter in High Security Mode.")
            return

        if len(self.user_attributes) >= MAX_NUM_USER_ATTRIBUTES:
            _logger.debug("Maximum number of custom attributes already added. Dropping attribute: %r=%r", key, value)
            return

        self.user_attributes[key] = value

    def _observe_exception(self, exc_info=None, ignore=None, expected=None, status_code=None):
        # Bail out if the transaction is not active or
        # collection of errors not enabled.

        transaction = self.transaction
        settings = transaction and transaction.settings

        if not settings:
            return

        if not settings.error_collector.enabled:
            return

        # At least one destination for error events must be enabled
        if not (
            settings.collect_traces
            or settings.collect_span_events
            or settings.collect_errors
            or settings.collect_error_events
        ):
            return

        # If no exception details provided, use current exception.

        # Pull from sys.exc_info if no exception is passed
        if not exc_info or None in exc_info:
            exc_info = sys.exc_info()

            # If no exception to report, exit
            if not exc_info or None in exc_info:
                return

        exc, value, tb = exc_info

        if getattr(value, "_nr_ignored", None):
            return

        module, name, fullnames, message = parse_exc_info((exc, value, tb))
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
        # 3. callable on transaction
        # 4. function parameter iterable of class names
        # 5. default rule matching from settings

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

        # Callable on transaction
        if should_ignore is None and hasattr(transaction, "_ignore_errors"):
            should_ignore = transaction._ignore_errors(exc, value, tb)
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
            should_ignore = should_ignore_error(exc_info, status_code=status_code, settings=settings)
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
            is_expected = is_expected_error(exc_info, status_code=status_code, settings=settings)

        # Record a supportability metric if error attributes are being
        # overiden.
        if "error.class" in self.agent_attributes:
            transaction._record_supportability("Supportability/SpanEvent/Errors/Dropped")

        # Add error details as agent attributes to span event.
        self._add_agent_attribute("error.class", fullname)
        self._add_agent_attribute("error.message", message)
        self._add_agent_attribute("error.expected", is_expected)

        return fullname, message, tb, is_expected

    def notice_error(self, error=None, attributes=None, expected=None, ignore=None, status_code=None):
        attributes = attributes if attributes is not None else {}

        recorded = self._observe_exception(
            error,
            ignore=ignore,
            expected=expected,
            status_code=status_code,
        )
        if recorded:
            fullname, message, tb, is_expected = recorded
            transaction = self.transaction
            settings = transaction and transaction.settings

            # Only add params if High Security Mode is off.

            custom_params = {}

            if settings.high_security:
                if attributes:
                    _logger.debug("Cannot add custom parameters in High Security Mode.")
            else:
                try:
                    for k, v in attributes.items():
                        name, val = process_user_attribute(k, v)
                        if name:
                            custom_params[name] = val
                except Exception:
                    _logger.debug(
                        "Parameters failed to validate for unknown "
                        "reason. Dropping parameters for error: %r. Check "
                        "traceback for clues.",
                        fullname,
                        exc_info=True,
                    )
                    custom_params = {}

            transaction._create_error_node(settings, fullname, message, is_expected, custom_params, self.guid, tb)

    def record_exception(self, exc_info=None, params=None, ignore_errors=None):
        # Deprecation Warning
        warnings.warn(
            ("The record_exception function is deprecated. Please use the new api named notice_error instead."),
            DeprecationWarning,
        )

        self.notice_error(error=exc_info, attributes=params, ignore=ignore_errors)

    def _add_agent_attribute(self, key, value):
        self.agent_attributes[key] = value

    def has_outstanding_children(self):
        return len(self.children) != self.child_count

    def _ready_to_complete(self):
        # we shouldn't continue if we're still running
        if not self.exited:
            return False

        # defer node completion until all children have exited
        if self.has_outstanding_children():
            return False

        return True

    def complete_trace(self):
        # This function is called only by children in the case that the node
        # creation has been deferred. _ready_to_complete should only return
        # True once the final child has completed.
        if self._ready_to_complete():
            self._complete_trace()

    def _complete_trace(self):
        # transaction already completed, this is an error
        if self.parent is None:
            _logger.error(
                "Runtime instrumentation error. The transaction "
                "already completed meaning a child called complete trace "
                "after the trace had been finalized. Trace: %r \n%s",
                self,
                "".join(traceback.format_stack()[:-1]),
            )

            return

        parent = self.parent

        # Check to see if we're async
        if parent.exited or parent.has_async_children:
            self.is_async = True

        # Pop ourselves as current node. If deferred, we have previously exited
        # and are being completed by a child trace.
        trace_cache().pop_current(self)

        # Wipe out parent reference so can't use object
        # again. Retain reference as local variable for use in
        # this call though.
        self.parent = None

        # wipe out exc data
        exc_data = self.exc_data
        self.exc_data = (None, None, None)

        # Observe errors on the span only if record_exception hasn't been
        # called already
        if exc_data[0] and "error.class" not in self.agent_attributes:
            self._observe_exception(exc_data)

        # Wipe out root reference as well
        transaction = self.root.transaction
        self.root = None

        # Give chance for derived class to finalize any data in
        # this object instance. The transaction is passed as a
        # parameter since the transaction object on this instance
        # will have been cleared above.

        self.finalize_data(transaction, *exc_data)
        exc_data = None

        # Give chance for derived class to create a standin node
        # object to be used in the transaction trace. If we get
        # one then give chance for transaction object to do
        # something with it, as well as our parent node.

        node = self.create_node()

        if node:
            transaction._process_node(node)
            parent.process_child(node, self.is_async)

        # ----------------------------------------------------------------------
        # SYNC  | The parent will not have exited yet, so no node will be
        #       | created. This operation is a NOP.
        # ----------------------------------------------------------------------
        # Async | The parent may have exited already while the child was
        #       | running. If this trace is the last node that's running, this
        #       | complete_trace will create the parent node.
        # ----------------------------------------------------------------------
        parent.complete_trace()

    def finalize_data(self, transaction, exc=None, value=None, tb=None):
        pass

    def create_node(self):
        return self

    def terminal_node(self):
        return False

    def update_async_exclusive_time(self, min_child_start_time, exclusive_duration):
        # if exited and the child started after, there's no overlap on the
        # exclusive time
        if self.exited and (self.end_time < min_child_start_time):
            exclusive_delta = 0.0
        # else there is overlap and we need to compute it
        elif self.exited:
            exclusive_delta = self.end_time - min_child_start_time

            # we don't want to double count the partial exclusive time
            # attributed to this trace, so we should reset the child start time
            # to after this trace ended
            min_child_start_time = self.end_time
        # we're still running so all exclusive duration is taken by us
        else:
            exclusive_delta = exclusive_duration

        # update the exclusive time
        self.exclusive -= exclusive_delta

        # pass any remaining exclusive duration up to the parent
        exclusive_duration_remaining = exclusive_duration - exclusive_delta

        if self.parent and exclusive_duration_remaining > 0.0:
            # call parent exclusive duration delta
            self.parent.update_async_exclusive_time(min_child_start_time, exclusive_duration_remaining)

    def process_child(self, node, is_async):
        self.children.append(node)
        if is_async:

            # record the lowest start time
            self.min_child_start_time = min(self.min_child_start_time, node.start_time)

            # if there are no children running, finalize exclusive time
            if self.child_count == len(self.children):

                exclusive_duration = node.end_time - self.min_child_start_time

                self.update_async_exclusive_time(self.min_child_start_time, exclusive_duration)

                # reset time range tracking
                self.min_child_start_time = float("inf")
        else:
            self.exclusive -= node.duration

    def increment_child_count(self):
        self.child_count += 1

        # if there's more than 1 child node outstanding
        # then the children are async w.r.t each other
        if (self.child_count - len(self.children)) > 1:
            self.has_async_children = True
        # else, the current trace that's being scheduled is not going to be
        # async. note that this implies that all previous traces have
        # completed
        else:
            self.has_async_children = False

    def get_linking_metadata(self):
        metadata = {
            "entity.type": "SERVICE",
        }
        txn = self.transaction
        if txn:
            metadata["span.id"] = self.guid
            metadata["trace.id"] = txn.trace_id
            settings = txn.settings
            if settings:
                metadata["entity.name"] = settings.app_name
                entity_guid = settings.entity_guid
                if entity_guid:
                    metadata["entity.guid"] = entity_guid
        return metadata


def add_custom_span_attribute(key, value):
    trace = current_trace()
    if trace:
        trace.add_custom_attribute(key, value)


def current_trace():
    return trace_cache().current_trace()


def get_linking_metadata():
    trace = current_trace()
    if trace:
        return trace.get_linking_metadata()
    else:
        return {
            "entity.type": "SERVICE",
        }


def record_exception(exc=None, value=None, tb=None, params=None, ignore_errors=None, application=None):
    # Deprecation Warning
    warnings.warn(
        ("The record_exception function is deprecated. Please use the new api named notice_error instead."),
        DeprecationWarning,
    )

    notice_error(error=(exc, value, tb), attributes=params, ignore=ignore_errors, application=application)


def notice_error(error=None, attributes=None, expected=None, ignore=None, status_code=None, application=None):
    if application is None:
        trace = current_trace()
        if trace:
            trace.notice_error(
                error=error,
                attributes=attributes,
                expected=expected,
                ignore=ignore,
                status_code=status_code,
            )
    else:
        if application.enabled:
            application.notice_error(
                error=error,
                attributes=attributes,
                expected=expected,
                ignore=ignore,
                status_code=status_code,
            )
