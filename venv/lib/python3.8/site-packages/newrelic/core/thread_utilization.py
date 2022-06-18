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

import time

from newrelic.samplers.decorators import data_source_factory

try:
    from newrelic.core._thread_utilization import ThreadUtilization
except ImportError:
    ThreadUtilization = None

_utilization_trackers = {}

def utilization_tracker(application):
    return _utilization_trackers.get(application)

class ThreadUtilizationDataSource(object):

    def __init__(self, application):
        self._consumer_name = application
        self._utilization_tracker = None
        self._last_timestamp = None
        self._utilization = None

    def start(self):
        if ThreadUtilization:
            utilization_tracker = ThreadUtilization()
            _utilization_trackers[self._consumer_name] = utilization_tracker
            self._utilization_tracker = utilization_tracker
            self._last_timestamp = time.time()
            self._utilization = self._utilization_tracker.utilization_count()

    def stop(self):
        try:
            self._utilization_tracker = None
            self._last_timestamp = None
            self._utilization = None
            del _utilization_trackers[self.source_name]
        except Exception:
            pass

    def __call__(self):
        if self._utilization_tracker is None:
            return

        now = time.time()

        # TODO This needs to be pushed down into _thread_utilization.c.
        # In doing that, need to fix up UtilizationClass count so the
        # reset is optional because in this case a read only variant is
        # needed for getting a per request custom metric of the
        # utilization during period of the request.
        #
        # TODO This currently doesn't take into consideration coroutines
        # and instance bust percentage is percentage of a single thread
        # and not of total available coroutines. Not sure whether can
        # generate something meaningful for coroutines. Also doesn't
        # work for asynchronous systems such as Twisted.

        new_utilization = self._utilization_tracker.utilization_count()

        elapsed_time = now - self._last_timestamp

        utilization = new_utilization - self._utilization

        utilization = utilization / elapsed_time

        self._last_timestamp = now
        self._utilization = new_utilization

        total_threads = None

        try:
            # Recent mod_wsgi versions publish the number of actual
            # threads so we can use this real value instead of the
            # calculated value. This is important in order to get the
            # correct utilization value for mod_wsgi daemon mode as the
            # way it manages the thread pool it may not actually
            # activate all available threads if the requirement isn't
            # there for them. Thus the utilization figure will be too
            # high as would only be calculated relative to the activated
            # threads and not the total of what is actually available.

            import mod_wsgi
            total_threads = mod_wsgi.threads_per_process

        except Exception:
            pass

        if total_threads is None:
            total_threads = self._utilization_tracker.total_threads()

        if total_threads:
            # Don't report any metrics if don't detect any threads
            # available and in use for handling web transactions,
            # otherwise we end up report zero metrics for task systems
            # such as Celery which skews the results wrongly.

            yield ('Instance/Available', total_threads)
            yield ('Instance/Used', utilization)

            busy = total_threads and utilization/total_threads or 0.0

            yield ('Instance/Busy', busy)

@data_source_factory(name='Thread Utilization')
def thread_utilization_data_source(settings, environ):
    return ThreadUtilizationDataSource(environ['consumer.name'])
