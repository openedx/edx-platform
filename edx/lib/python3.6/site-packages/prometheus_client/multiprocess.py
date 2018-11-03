#!/usr/bin/python

from __future__ import unicode_literals

from collections import defaultdict
import glob
import json
import os

from . import core


class MultiProcessCollector(object):
    """Collector for files for multi-process mode."""

    def __init__(self, registry, path=None):
        if path is None:
            path = os.environ.get('prometheus_multiproc_dir')
        if not path or not os.path.isdir(path):
            raise ValueError('env prometheus_multiproc_dir is not set or not a directory')
        self._path = path
        if registry:
            registry.register(self)

    def collect(self):
        files = glob.glob(os.path.join(self._path, '*.db'))
        return self.merge(files, accumulate=True)

    def merge(self, files, accumulate=True):
        """Merge metrics from given mmap files.

        By default, histograms are accumulated, as per prometheus wire format.
        But if writing the merged data back to mmap files, use
        accumulate=False to avoid compound accumulation.
        """
        metrics = {}
        for f in files:
            parts = os.path.basename(f).split('_')
            typ = parts[0]
            d = core._MmapedDict(f, read_mode=True)
            for key, value in d.read_all_values():
                metric_name, name, labels = json.loads(key)
                labels_key = tuple(sorted(labels.items()))

                metric = metrics.get(metric_name)
                if metric is None:
                    metric = core.Metric(metric_name, 'Multiprocess metric', typ)
                    metrics[metric_name] = metric

                if typ == 'gauge':
                    pid = parts[2][:-3]
                    metric._multiprocess_mode = parts[1]
                    metric.add_sample(name, labels_key + (('pid', pid), ), value)
                else:
                    # The duplicates and labels are fixed in the next for.
                    metric.add_sample(name, labels_key, value)
            d.close()

        for metric in metrics.values():
            samples = defaultdict(float)
            buckets = {}
            for s in metric.samples:
                name, labels, value = s.name, s.labels, s.value
                if metric.type == 'gauge':
                    without_pid = tuple(l for l in labels if l[0] != 'pid')
                    if metric._multiprocess_mode == 'min':
                        current = samples.setdefault((name, without_pid), value)
                        if value < current:
                            samples[(s.name, without_pid)] = value
                    elif metric._multiprocess_mode == 'max':
                        current = samples.setdefault((name, without_pid), value)
                        if value > current:
                            samples[(s.name, without_pid)] = value
                    elif metric._multiprocess_mode == 'livesum':
                        samples[(name, without_pid)] += value
                    else:  # all/liveall
                        samples[(name, labels)] = value

                elif metric.type == 'histogram':
                    bucket = tuple(float(l[1]) for l in labels if l[0] == 'le')
                    if bucket:
                        # _bucket
                        without_le = tuple(l for l in labels if l[0] != 'le')
                        buckets.setdefault(without_le, {})
                        buckets[without_le].setdefault(bucket[0], 0.0)
                        buckets[without_le][bucket[0]] += value
                    else:
                        # _sum/_count
                        samples[(s.name, labels)] += value

                else:
                    # Counter and Summary.
                    samples[(s.name, labels)] += value

            # Accumulate bucket values.
            if metric.type == 'histogram':
                for labels, values in buckets.items():
                    acc = 0.0
                    for bucket, value in sorted(values.items()):
                        sample_key = (
                            metric.name + '_bucket',
                            labels + (('le', core._floatToGoString(bucket)), ),
                        )
                        if accumulate:
                            acc += value
                            samples[sample_key] = acc
                        else:
                            samples[sample_key] = value
                    if accumulate:
                        samples[(metric.name + '_count', labels)] = acc

            # Convert to correct sample format.
            metric.samples = [core.Sample(name, dict(labels), value) for (name, labels), value in samples.items()]
        return metrics.values()


def mark_process_dead(pid, path=None):
    """Do bookkeeping for when one process dies in a multi-process setup."""
    if path is None:
        path = os.environ.get('prometheus_multiproc_dir')
    for f in glob.glob(os.path.join(path, 'gauge_livesum_{0}.db'.format(pid))):
        os.remove(f)
    for f in glob.glob(os.path.join(path, 'gauge_liveall_{0}.db'.format(pid))):
        os.remove(f)
