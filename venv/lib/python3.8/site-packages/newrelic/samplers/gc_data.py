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

import gc
import os
import platform
import time
from collections import Counter

from newrelic.common.object_names import callable_name
from newrelic.core.config import global_settings
from newrelic.core.stats_engine import CustomMetrics
from newrelic.samplers.decorators import data_source_factory


@data_source_factory(name="Garbage Collector Metrics")
class _GCDataSource(object):
    def __init__(self, settings, environ):
        self.gc_time_metrics = CustomMetrics()
        self.start_time = 0.0
        self.previous_stats = {}
        self.pid = os.getpid()

    @property
    def enabled(self):
        settings = global_settings()
        if platform.python_implementation() == "PyPy" or not settings:
            return False
        else:
            return settings.gc_runtime_metrics.enabled

    @property
    def top_object_count_limit(self):
        settings = global_settings()
        return settings.gc_runtime_metrics.top_object_count_limit

    def record_gc(self, phase, info):
        if not self.enabled:
            return

        current_generation = info["generation"]

        if phase == "start":
            self.start_time = time.time()
        elif phase == "stop":
            total_time = time.time() - self.start_time
            self.gc_time_metrics.record_custom_metric("GC/time/%d/all" % self.pid, total_time)
            for gen in range(0, 3):
                if gen <= current_generation:
                    self.gc_time_metrics.record_custom_metric("GC/time/%d/%d" % (self.pid, gen), total_time)
                else:
                    self.gc_time_metrics.record_custom_metric("GC/time/%d/%d" % (self.pid, gen), 0)

    def start(self):
        if hasattr(gc, "callbacks"):
            gc.callbacks.append(self.record_gc)

    def stop(self):
        # The callback must be removed before resetting the metrics tables.
        # If it isn't, it's possible to be interrupted by the gc and to have more
        # metrics appear in the table that should be empty.
        if hasattr(gc, "callbacks") and self.record_gc in gc.callbacks:
            gc.callbacks.remove(self.record_gc)

        self.gc_time_metrics.reset_metric_stats()
        self.start_time = 0.0

    def __call__(self):
        if not self.enabled:
            return

        # Record object count in total and per generation
        if hasattr(gc, "get_count"):
            counts = gc.get_count()
            yield ("GC/objects/%d/all" % self.pid, {"count": sum(counts)})
            for gen, count in enumerate(counts):
                yield (
                    "GC/objects/%d/generation/%d" % (self.pid, gen),
                    {"count": count},
                )

        # Record object count for top five types with highest count
        if hasattr(gc, "get_objects"):
            object_types = map(type, gc.get_objects())
            if self.top_object_count_limit > 0:
                highest_types = Counter(object_types).most_common(self.top_object_count_limit)
                for obj_type, count in highest_types:
                    yield (
                        "GC/objects/%d/type/%s" % (self.pid, callable_name(obj_type)),
                        {"count": count},
                    )

        if hasattr(gc, "get_stats"):
            stats_by_gen = gc.get_stats()
            if isinstance(stats_by_gen, list):
                for stat_name in stats_by_gen[0].keys():
                    # Aggregate metrics for /all
                    count = sum(stats[stat_name] for stats in stats_by_gen)
                    previous_value = self.previous_stats.get((stat_name, "all"), 0)
                    self.previous_stats[(stat_name, "all")] = count
                    change_in_value = count - previous_value
                    yield (
                        "GC/%s/%d/all" % (stat_name, self.pid),
                        {"count": change_in_value},
                    )

                    # Breakdowns by generation
                    for gen, stats in enumerate(stats_by_gen):
                        previous_value = self.previous_stats.get((stat_name, gen), 0)
                        self.previous_stats[(stat_name, gen)] = stats[stat_name]
                        change_in_value = stats[stat_name] - previous_value

                        yield (
                            "GC/%s/%d/%d" % (stat_name, self.pid, gen),
                            {"count": change_in_value},
                        )

        # In order to avoid a concurrency issue with getting interrupted by the
        # garbage collector, we save a reference to the old metrics table, and overwrite
        # self.gc_time_metrics with a new empty table via reset_metric_stats().
        # This guards against losing data points, or having inconsistent data points
        # reported between /all and the totals of /generation/%d metrics.
        gc_time_metrics = self.gc_time_metrics.metrics()
        self.gc_time_metrics.reset_metric_stats()

        for metric in gc_time_metrics:
            raw_metric = metric[1]
            yield metric[0], {
                "count": raw_metric.call_count,
                "total": raw_metric.total_call_time,
                "min": raw_metric.min_call_time,
                "max": raw_metric.max_call_time,
                "sum_of_squares": raw_metric.sum_of_squares,
            }


garbage_collector_data_source = _GCDataSource
