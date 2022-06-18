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

"""This module implements a data source for generating metrics about CPU
usage.

"""

import os

from newrelic.common.system_info import logical_processor_count
from newrelic.common.stopwatch import start_timer

from newrelic.samplers.decorators import data_source_factory

@data_source_factory(name='CPU Usage')
class _CPUUsageDataSource(object):

    def __init__(self, settings, environ):
        self._timer = None
        self._times = None

    def start(self):
        self._timer = start_timer()
        try:
            self._times = os.times()
        except Exception:
            self._times = None

    def stop(self):
        self._timer = None
        self._times = None

    def __call__(self):
        if self._times is None:
            return

        new_times = os.times()
        elapsed_time = self._timer.restart_timer()
        elapsed_cpu_time = elapsed_time*logical_processor_count()

        user_time = new_times[0] - self._times[0]
        user_utilization = user_time / elapsed_cpu_time

        system_time = new_times[1] - self._times[1]
        system_utilization = system_time / elapsed_cpu_time

        total_time = sum(new_times[0:4]) - sum(self._times[0:4])
        total_utilization = total_time / elapsed_cpu_time

        self._times = new_times

        yield ('CPU/User Time', user_time)
        yield ('CPU/User/Utilization', user_utilization)
        yield ('CPU/System Time', system_time)
        yield ('CPU/System/Utilization', system_utilization)
        yield ('CPU/Total Time', total_time)
        yield ('CPU/Total/Utilization', total_utilization)

cpu_usage_data_source = _CPUUsageDataSource
