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

"""This module implements a global cache for tracking any traces.

"""

import logging
import random
import sys
import threading
import traceback
import weakref

try:
    import thread
except ImportError:
    import _thread as thread

from newrelic.core.config import global_settings
from newrelic.core.loop_node import LoopNode

_logger = logging.getLogger(__name__)


def current_task(asyncio):
    if not asyncio:
        return

    current_task = getattr(asyncio, "current_task", None)
    if current_task is None:
        current_task = getattr(asyncio.Task, "current_task", None)

    try:
        return current_task()
    except:
        pass


def all_tasks(asyncio):
    if not asyncio:
        return

    all_tasks = getattr(asyncio, "all_tasks", None)
    if all_tasks is None:
        all_tasks = getattr(asyncio.Task, "all_tasks", None)

    try:
        return all_tasks()
    except:
        pass


def get_event_loop(task):
    get_loop = getattr(task, "get_loop", None)
    if get_loop:
        return get_loop()
    return getattr(task, "_loop", None)


class cached_module(object):
    def __init__(self, module_path, name=None):
        self.module_path = module_path
        self.name = name or module_path

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        module = sys.modules.get(self.module_path)
        if module:
            instance.__dict__[self.name] = module
            return module


class TraceCacheNoActiveTraceError(RuntimeError):
    pass


class TraceCacheActiveTraceError(RuntimeError):
    pass


class TraceCache(object):
    asyncio = cached_module("asyncio")
    greenlet = cached_module("greenlet")

    def __init__(self):
        self._cache = weakref.WeakValueDictionary()

    def __repr__(self):
        return "<%s object at 0x%x %s>" % (self.__class__.__name__, id(self), str(dict(self._cache.items())))

    def current_thread_id(self):
        """Returns the thread ID for the caller.

        When greenlets are present and we detect we are running in the
        greenlet then we use the greenlet ID instead of the thread ID.

        """

        if self.greenlet:
            # Greenlet objects are maintained in a tree structure with
            # the 'parent' attribute pointing to that which a specific
            # instance is associated with. Only the root node has no
            # parent. This node is special and is the one which
            # corresponds to the original thread where the greenlet
            # module was imported and initialised. That root greenlet is
            # never actually running and we should always ignore it. In
            # all other cases where we can obtain a current greenlet,
            # then it should indicate we are running as a greenlet.

            current = self.greenlet.getcurrent()
            if current is not None and current.parent:
                return id(current)

        if self.asyncio:
            task = current_task(self.asyncio)
            if task is not None:
                return id(task)

        return thread.get_ident()

    def task_start(self, task):
        trace = self.current_trace()
        if trace:
            self._cache[id(task)] = trace

    def task_stop(self, task):
        self._cache.pop(id(task), None)

    def current_transaction(self):
        """Return the transaction object if one exists for the currently
        executing thread.

        """

        trace = self._cache.get(self.current_thread_id())
        return trace and trace.transaction

    def current_trace(self):
        return self._cache.get(self.current_thread_id())

    def active_threads(self):
        """Returns an iterator over all current stack frames for all
        active threads in the process. The result for each is a tuple
        consisting of the thread identifier, a categorisation of the
        type of thread, and the stack frame. Note that we actually treat
        any greenlets as threads as well. In that case the thread ID is
        the id() of the greenlet.

        This is in this class for convenience as needs to access the
        currently active transactions to categorise transaction threads
        as being for web transactions or background tasks.

        """

        # First yield up those for real Python threads.

        for thread_id, frame in sys._current_frames().items():
            trace = self._cache.get(thread_id)
            transaction = trace and trace.transaction
            if transaction is not None:
                if transaction.background_task:
                    yield transaction, thread_id, "BACKGROUND", frame
                else:
                    yield transaction, thread_id, "REQUEST", frame
            else:
                # Note that there may not always be a thread object.
                # This is because thread could have been created direct
                # against the thread module rather than via the high
                # level threading module. Categorise anything we can't
                # obtain a name for as being 'OTHER'.

                thread = threading._active.get(thread_id)
                if thread is not None and thread.getName().startswith("NR-"):
                    yield None, thread_id, "AGENT", frame
                else:
                    yield None, thread_id, "OTHER", frame

        # Now yield up those corresponding to greenlets. Right now only
        # doing this for greenlets in which any active transactions are
        # running. We don't have a way of knowing what non transaction
        # threads are running.

        debug = global_settings().debug

        if debug.enable_coroutine_profiling:
            for thread_id, trace in self._cache.items():
                transaction = trace.transaction
                if transaction and transaction._greenlet is not None:
                    gr = transaction._greenlet()
                    if gr and gr.gr_frame is not None:
                        if transaction.background_task:
                            yield (transaction, thread_id, "BACKGROUND", gr.gr_frame)
                        else:
                            yield (transaction, thread_id, "REQUEST", gr.gr_frame)

    def prepare_for_root(self):
        """Updates the cache state so that a new root can be created if the
        trace in the cache is from a different task (for asyncio). Returns the
        current trace after the cache is updated."""
        thread_id = self.current_thread_id()
        trace = self._cache.get(thread_id)
        if not trace:
            return None

        if not hasattr(trace, "_task"):
            return trace

        task = current_task(self.asyncio)
        if task is not None and id(trace._task) != id(task):
            self._cache.pop(thread_id, None)
            return None

        if trace.root and trace.root.exited:
            self._cache.pop(thread_id, None)
            return None

        return trace

    def save_trace(self, trace):
        """Saves the specified trace away under the thread ID of
        the current executing thread. Will also cache a reference to the
        greenlet if using coroutines. This is so we can later determine
        the stack trace for a transaction when using greenlets.

        """

        thread_id = trace.thread_id

        if thread_id in self._cache:
            cache_root = self._cache[thread_id].root
            if cache_root and cache_root is not trace.root and not cache_root.exited:
                # Cached trace exists and has a valid root still
                _logger.error(
                    "Runtime instrumentation error. Attempt to "
                    "save a trace from an inactive transaction. "
                    "Report this issue to New Relic support.\n%s",
                    "".join(traceback.format_stack()[:-1]),
                )

                raise TraceCacheActiveTraceError("transaction already active")

        self._cache[thread_id] = trace

        # We judge whether we are actually running in a coroutine by
        # seeing if the current thread ID is actually listed in the set
        # of all current frames for executing threads. If we are
        # executing within a greenlet, then thread.get_ident() will
        # return the greenlet identifier. This will not be a key in
        # dictionary of all current frames because that will still be
        # the original standard thread which all greenlets are running
        # within.

        trace._greenlet = None

        if hasattr(sys, "_current_frames"):
            if thread_id not in sys._current_frames():
                if self.greenlet:
                    trace._greenlet = weakref.ref(self.greenlet.getcurrent())

                if self.asyncio and not hasattr(trace, "_task"):
                    task = current_task(self.asyncio)
                    trace._task = task

    def pop_current(self, trace):
        """Restore the trace's parent under the thread ID of the current
        executing thread."""

        if hasattr(trace, "_task"):
            delattr(trace, "_task")

        thread_id = trace.thread_id
        parent = trace.parent
        self._cache[thread_id] = parent

    def complete_root(self, root):
        """Completes a trace specified by the given root

        Drops the specified root, validating that it is
        actually saved away under the current executing thread.

        """

        if hasattr(root, "_task"):
            if root.has_outstanding_children():
                task_ids = (id(task) for task in all_tasks(self.asyncio))

                to_complete = []

                for task_id in task_ids:
                    entry = self._cache.get(task_id)

                    if entry and entry is not root and entry.root is root:
                        to_complete.append(entry)

                while to_complete:
                    entry = to_complete.pop()
                    if entry.parent and entry.parent is not root:
                        to_complete.append(entry.parent)
                    entry.__exit__(None, None, None)

            root._task = None

        thread_id = root.thread_id

        if thread_id not in self._cache:
            thread_id = self.current_thread_id()
            if thread_id not in self._cache:
                raise TraceCacheNoActiveTraceError("no active trace")

        current = self._cache.get(thread_id)

        if root is not current:
            _logger.error(
                "Runtime instrumentation error. Attempt to "
                "drop the root when it is not the current "
                "trace. Report this issue to New Relic support.\n%s",
                "".join(traceback.format_stack()[:-1]),
            )

            raise RuntimeError("not the current trace")

        del self._cache[thread_id]
        root._greenlet = None

    def record_event_loop_wait(self, start_time, end_time):
        transaction = self.current_transaction()
        if not transaction or not transaction.settings:
            return

        settings = transaction.settings.event_loop_visibility

        if not settings.enabled:
            return

        duration = end_time - start_time
        transaction._loop_time += duration

        if duration < settings.blocking_threshold:
            return

        fetch_name = transaction._cached_path.path
        roots = set()
        seen = set()

        task = getattr(transaction.root_span, "_task", None)
        loop = get_event_loop(task)

        for trace in self._cache.values():
            if trace in seen:
                continue

            # If the trace is on a different transaction and it's asyncio
            if (
                trace.transaction is not transaction
                and getattr(trace, "_task", None) is not None
                and get_event_loop(trace._task) is loop
                and trace._is_leaf()
            ):
                trace.exclusive -= duration
                roots.add(trace.root)
                seen.add(trace)

        seen = None

        for root in roots:
            guid = "%016x" % random.getrandbits(64)
            node = LoopNode(
                fetch_name=fetch_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                guid=guid,
            )
            transaction = root.transaction
            transaction._process_node(node)
            root.increment_child_count()
            root.add_child(node)


_trace_cache = TraceCache()


def trace_cache():
    return _trace_cache


def greenlet_loaded(module):
    _trace_cache.greenlet = module


def asyncio_loaded(module):
    _trace_cache.asyncio = module
