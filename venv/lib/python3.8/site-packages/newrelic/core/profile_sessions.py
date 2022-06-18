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

import base64
import logging
import os
import threading
import time
import zlib
from collections import defaultdict, deque

import newrelic
import newrelic.packages.six as six
from newrelic.common.encoding_utils import json_encode
from newrelic.core.config import global_settings
from newrelic.core.trace_cache import trace_cache

try:
    from sys import intern
except ImportError:
    pass

_logger = logging.getLogger(__name__)

AGENT_PACKAGE_DIRECTORY = os.path.dirname(newrelic.__file__) + "/"


class SessionState(object):
    RUNNING = 1
    FINISHED = 2


def format_stack_trace(frame, thread_category):
    """Formats the frame obj into a list of stack trace tuples."""

    stack_trace = deque()

    while frame:
        # The value frame.f_code.co_firstlineno is the first line of
        # code in the file for the specified function. The value
        # frame.f_lineno is the actual line which is being executed
        # at the time the stack frame was being viewed.

        code = frame.f_code

        filename = intern(code.co_filename)
        func_name = intern(code.co_name)
        first_line = code.co_firstlineno

        real_line = frame.f_lineno

        # Set ourselves up to process next frame back up the stack.

        frame = frame.f_back

        # So as to make it more obvious to the user as to what their
        # code is doing, we drop out stack frames related to the
        # agent instrumentation. Don't do this for the agent threads
        # though as we still need to seem them in that case so can
        # debug what the agent itself is doing.

        if thread_category != "AGENT" and filename.startswith(AGENT_PACKAGE_DIRECTORY):
            continue

        if not stack_trace:
            # Add the fake leaf node with line number of where the
            # code was executing at the point of the sample. This
            # could be actual Python code within the function, or
            # more likely showing the point where a call is being
            # made into a C function wrapped as Python object. The
            # latter can occur because we will not see stack frames
            # when calling into C functions.

            stack_trace.appendleft((filename, func_name, real_line, real_line))

        # Add the actual node for the function being called at this
        # level in the stack frames.

        stack_trace.appendleft((filename, func_name, first_line, real_line))

    return stack_trace


def collect_stack_traces(include_nr_threads=False):
    """Generator that yields the (thread category, stack trace) of all the
    python threads.

    """
    for (txn, thread_id, thread_category, frame) in trace_cache().active_threads():

        # Skip NR Threads unless explicitly requested.

        if (thread_category == "AGENT") and (not include_nr_threads):
            continue

        stack_trace = format_stack_trace(frame, thread_category)

        # Skip over empty stack traces. This is merely for optimization.
        #
        # It saves us from adding an empty deque to the txn obj, which will be
        # discarded later on during call tree merge.

        if not stack_trace:
            continue

        yield thread_category, stack_trace


class ProfileSessionManager(object):
    """Singleton class that manages multiple profile sessions. Do NOT
    instantiate directly from this class. Instead use profile_session_manager()

    """

    _lock = threading.Lock()
    _instance = None

    @staticmethod
    def singleton():
        with ProfileSessionManager._lock:
            if ProfileSessionManager._instance is None:
                ProfileSessionManager._instance = ProfileSessionManager()

        return ProfileSessionManager._instance

    def __init__(self):
        self.full_profile_session = None

        # Name of the application that requested the full_profile session.

        self.full_profile_app = None

        self.finished_sessions = defaultdict(list)

        self._profiler_shutdown = threading.Event()
        self._profiler_thread = None
        self._profiler_thread_running = False
        self._lock = threading.Lock()
        self.profile_agent_code = False
        self.sample_period_s = 0.1

    def start_profile_session(self, app_name, profile_id, stop_time, sample_period_s=0.1, profile_agent_code=False):
        """Start a new profiler session. If a full_profiler is already
        running, do nothing and return false.

        """

        # XXX Only one instance of this at the moment. Also only one harvest
        # thread so do not need thread locking. If we move to multiple harvest
        # threads, would need locking.

        # Only one full profile session can run at any given time.

        if self.full_profile_session:
            # log an error message
            return False

        # Acquire thread lock before updating the data structures. This method
        # is invoked from the harvest thread and this ensures the variables are
        # not being updated concurrently by the profiler thread.

        with self._lock:

            self.profile_agent_code = profile_agent_code
            self.sample_period_s = sample_period_s
            self.full_profile_session = ProfileSession(profile_id, stop_time)
            self.full_profile_app = app_name

            # Create a background thread to collect stack traces. Do this only
            # if a background thread doesn't already exist.

            if not self._profiler_thread_running:
                self._profiler_thread = threading.Thread(target=self._profiler_loop, name="NR-Profiler-Thread")
                self._profiler_thread.daemon = True

                self._profiler_thread.start()
                self._profiler_thread_running = True

        return True

    def stop_profile_session(self, app_name):
        """Stop a profiler session and return True when successful. Set key_txn
        to None to stop the full_profile_session. Returns False if no profiler
        sessions were stopped.

        """

        # Grab the lock before updating the profile sessions. This is to
        # make sure that we're not updating the data structures while the
        # harvest thread is starting/stopping new sessions.

        with self._lock:
            if (self.full_profile_session is not None) and (app_name == self.full_profile_app):
                self.full_profile_session.state = SessionState.FINISHED
                self.full_profile_session.actual_stop_time_s = time.time()
                self.finished_sessions[app_name].append(self.full_profile_session)
                self.full_profile_session = None
                self.full_profile_app = None

            else:
                # log an error message
                return False

    def profile_data(self, app_name):
        """Generator that yields the profile data in the form of call tree.
        Data from full profiler will only be returned when the profiler has
        finished. When no data is available None will be returned.

        """
        with self._lock:
            for session in self.finished_sessions[app_name]:
                _logger.debug(
                    "Reporting final thread profiling data for "
                    "%d transactions over a period of %.2f seconds "
                    "and %d samples.",
                    session.transaction_count,
                    time.time() - session.start_time_s,
                    session.sample_count,
                )

                yield session.profile_data()

            # After reporting data on the finished_sessions empty the
            # finished_sessions list.

            self.finished_sessions.pop(app_name)

    def _profiler_loop(self):
        """Infinite loop that wakes up periodically to collect stack traces,
        merge it into call tree if necessary, finally update the state of all
        the active profile sessions.

        """

        while True:

            for category, stack in collect_stack_traces(self.profile_agent_code):

                # Merge the stack_trace to the call tree only for
                # full_profile_session.

                if self.full_profile_session:
                    self.full_profile_session.update_call_tree(category, stack)

            self.update_profile_sessions()

            # Stop the profiler thread if there are no profile sessions.

            if self.full_profile_session is None:
                self._profiler_thread_running = False
                return

            self._profiler_shutdown.wait(self.sample_period_s)

    def update_profile_sessions(self):
        """Check the current time and decide if any of the profile sessions
        have expired and move it to the finished_sessions list.

        """

        if self.full_profile_session:
            self.full_profile_session.sample_count += 1
            if time.time() >= self.full_profile_session.stop_time_s:
                self.stop_profile_session(self.full_profile_app)
                _logger.info("Finished thread profiling session.")

    def shutdown(self, app_name):
        """Stop all profile sessions running on the given app_name."""

        # Check if we need to stop the full profiler.

        if app_name == self.full_profile_app:
            self.stop_profile_session(app_name)

        return True


class ProfileSession(object):
    def __init__(self, profile_id, stop_time):
        self.profile_id = profile_id
        self.start_time_s = time.time()
        self.stop_time_s = stop_time
        self.actual_stop_time_s = 0
        self.state = SessionState.RUNNING
        self.reset_profile_data()

    def reset_profile_data(self):
        self.call_buckets = {"REQUEST": {}, "AGENT": {}, "BACKGROUND": {}, "OTHER": {}}
        self._node_list = []
        self.start_time_s = time.time()
        self.sample_count = 0
        self.transaction_count = 0

    def update_call_tree(self, bucket_type, stack_trace):
        """Merge a single call stack trace into a call tree bucket. If
        no appropriate call tree is found then create a new call tree.
        An appropriate call tree will have the same root node as the
        last method in the stack trace.

        """

        self.transaction_count += 1

        depth = 1
        try:
            bucket = self.call_buckets[bucket_type]
        except KeyError:
            return False

        for method in stack_trace:
            call_tree = bucket.get(method)

            if call_tree is None:
                call_tree = CallTree(method, depth=depth)
                self._node_list.append(call_tree)
                bucket[method] = call_tree

            call_tree.call_count += 1

            # The call depth is incremented on each recursive call so we
            # know the depth of the call stack. We use this later when
            # pruning nodes if go over the limit. Specifically, the deepest
            # and least used nodes will be prune first.

            bucket = call_tree.children
            depth += 1

        return True

    def _prune_call_trees(self, limit):
        """Prune the number of profile nodes we send up to the data
        collector down to the specified limit. Done to ensure not
        sending so much data that gets reject for being over size limit.

        """

        if len(self._node_list) <= limit:
            return

        # We sort the profile nodes based on call count, but also take
        # into consideration the depth of the node in the call tree.
        # Based on sort order, we then ignore any nodes over our limit.
        #
        # We include depth as that way we try and trim the deepest and
        # least visited leaf nodes first. If we don't do this, then
        # depending on how sorting orders nodes with same call count, we
        # could ignore a parent node high up in call chain even though
        # children weren't being ignored and so effectively ignore more
        # than the minimum we need to. Granted this would only occur
        # where was a linear call tree where all had the same call count,
        # such as may occur with recursion.
        #
        # Also note that we still can actually end up with less nodes in
        # the end being displayed in the UI than the limit being applied
        # even though we initially cutoff at the limit. This is because
        # we are looking at nodes from different categories before they
        # have been merged together. If a node appears at same relative
        # position in multiple categories, then when displaying multiple
        # categories in UI, the duplicates only appear as one after the
        # UI merges them.

        self._node_list.sort(key=lambda x: (x.call_count, -x.depth), reverse=True)

        for node in self._node_list[limit:]:
            node.ignore = True

    def profile_data(self):

        # Generic profiling sessions have to wait for completion before
        # reporting data.

        if self.state == SessionState.RUNNING:
            return None

        # We prune the number of nodes sent if we are over the specified
        # limit. This is just to avoid having the response be too large
        # and get rejected by the data collector.

        settings = global_settings()
        self._prune_call_trees(settings.agent_limits.thread_profiler_nodes)

        flat_tree = {}
        thread_count = 0

        for category, bucket in six.iteritems(self.call_buckets):

            # Only flatten buckets that have data in them. No need to send
            # empty buckets.

            if bucket:
                flat_tree[category] = [x.flatten() for x in bucket.values()]
                thread_count += len(bucket)

        # Construct the actual final data for sending. The actual call
        # data is turned into JSON, compressed and then base64 encoded at
        # this point to cut its size.

        if settings.debug.log_thread_profile_payload:
            _logger.debug("Encoding thread profile data where payload=%r.", flat_tree)

        json_call_tree = json_encode(flat_tree)

        level = settings.agent_limits.data_compression_level
        level = level or zlib.Z_DEFAULT_COMPRESSION

        encoded_tree = base64.standard_b64encode(zlib.compress(six.b(json_call_tree), level))

        if six.PY3:
            encoded_tree = encoded_tree.decode("Latin-1")

        profile = [
            [
                self.profile_id,
                self.start_time_s * 1000,
                (self.actual_stop_time_s or time.time()) * 1000,
                self.sample_count,
                encoded_tree,
                thread_count,
                0,
                None,
            ]
        ]

        # Reset the data structures to default.

        self.reset_profile_data()
        return profile


class CallTree(object):
    def __init__(self, method_data, call_count=0, depth=1):
        self.method_data = method_data
        self.call_count = call_count
        self.children = {}

        self.depth = depth
        self.ignore = False

    def flatten(self):
        filename, func_name, func_line, exec_line = self.method_data

        # func_line is the first line of a function and exec_line is the line
        # inside that function that is currently being executed.  On the leaf
        # nodes the exec_line will be different from the func_line. Such nodes
        # are labeled with an @ sign in the second element of the tuple.

        if func_line == exec_line:
            method_data = (filename, "@%s#%s" % (func_name, func_line), exec_line)
        else:
            method_data = (filename, "%s#%s" % (func_name, func_line), exec_line)

        return [method_data, self.call_count, 0, [x.flatten() for x in self.children.values() if not x.ignore]]


def profile_session_manager():
    return ProfileSessionManager.singleton()
