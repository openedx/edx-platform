#!/usr/bin/python

from __future__ import unicode_literals

from collections import namedtuple
import copy
import json
import math
import mmap
import os
import re
import struct
import sys
from threading import Lock
import time
from timeit import default_timer
import types

from .decorator import decorate

if sys.version_info > (3,):
    unicode = str

_METRIC_NAME_RE = re.compile(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$')
_METRIC_LABEL_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
_RESERVED_METRIC_LABEL_NAME_RE = re.compile(r'^__.*$')
_INF = float("inf")
_MINUS_INF = float("-inf")
_INITIAL_MMAP_SIZE = 1 << 20

_pack_integer_func = struct.Struct(b'i').pack
_pack_double_func = struct.Struct(b'd').pack
_unpack_integer = struct.Struct(b'i').unpack_from
_unpack_double = struct.Struct(b'd').unpack_from

# Timestamp and exemplar are optional.
# Value can be an int or a float.
# Timestamp can be a float containing a unixtime in seconds,
# a Timestamp object, or None.
# Exemplar can be an Exemplar object, or None.
Sample = namedtuple('Sample', ['name', 'labels', 'value', 'timestamp', 'exemplar'])
Sample.__new__.__defaults__ = (None, None)


class Timestamp(object):
    '''A nanosecond-resolution timestamp.'''

    def __init__(self, sec, nsec):
        if nsec < 0 or nsec >= 1e9:
            raise ValueError("Invalid value for nanoseconds in Timestamp: {}".format(nsec))
        if sec < 0:
            nsec = -nsec
        self.sec = int(sec)
        self.nsec = int(nsec)

    def __str__(self):
        return "{0}.{1:09d}".format(self.sec, self.nsec)

    def __repr__(self):
        return "Timestamp({0}, {1})".format(self.sec, self.nsec)

    def __float__(self):
        return float(self.sec) + float(self.nsec) / 1e9

    def __eq__(self, other):
        return type(self) == type(other) and self.sec == other.sec and self.nsec == other.nsec

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        return self.sec > other.sec or self.nsec > other.nsec


Exemplar = namedtuple('Exemplar', ['labels', 'value', 'timestamp'])
Exemplar.__new__.__defaults__ = (None,)


class CollectorRegistry(object):
    '''Metric collector registry.

    Collectors must have a no-argument method 'collect' that returns a list of
    Metric objects. The returned metrics should be consistent with the Prometheus
    exposition formats.
    '''

    def __init__(self, auto_describe=False):
        self._collector_to_names = {}
        self._names_to_collectors = {}
        self._auto_describe = auto_describe
        self._lock = Lock()

    def register(self, collector):
        '''Add a collector to the registry.'''
        with self._lock:
            names = self._get_names(collector)
            duplicates = set(self._names_to_collectors).intersection(names)
            if duplicates:
                raise ValueError(
                    'Duplicated timeseries in CollectorRegistry: {0}'.format(
                        duplicates))
            for name in names:
                self._names_to_collectors[name] = collector
            self._collector_to_names[collector] = names

    def unregister(self, collector):
        '''Remove a collector from the registry.'''
        with self._lock:
            for name in self._collector_to_names[collector]:
                del self._names_to_collectors[name]
            del self._collector_to_names[collector]

    def _get_names(self, collector):
        '''Get names of timeseries the collector produces.'''
        desc_func = None
        # If there's a describe function, use it.
        try:
            desc_func = collector.describe
        except AttributeError:
            pass
        # Otherwise, if auto describe is enabled use the collect function.
        if not desc_func and self._auto_describe:
            desc_func = collector.collect

        if not desc_func:
            return []

        result = []
        type_suffixes = {
            'counter': ['_total', '_created'],
            'summary': ['', '_sum', '_count', '_created'],
            'histogram': ['_bucket', '_sum', '_count', '_created'],
            'gaugehistogram': ['_bucket', '_gsum', '_gcount'],
            'info': ['_info'],
        }
        for metric in desc_func():
            for suffix in type_suffixes.get(metric.type, ['']):
                result.append(metric.name + suffix)
        return result

    def collect(self):
        '''Yields metrics from the collectors in the registry.'''
        collectors = None
        with self._lock:
            collectors = copy.copy(self._collector_to_names)
        for collector in collectors:
            for metric in collector.collect():
                yield metric

    def restricted_registry(self, names):
        '''Returns object that only collects some metrics.

        Returns an object which upon collect() will return
        only samples with the given names.

        Intended usage is:
            generate_latest(REGISTRY.restricted_registry(['a_timeseries']))

        Experimental.'''
        names = set(names)
        collectors = set()
        with self._lock:
            for name in names:
                if name in self._names_to_collectors:
                    collectors.add(self._names_to_collectors[name])
        metrics = []
        for collector in collectors:
            for metric in collector.collect():
                samples = [s for s in metric.samples if s[0] in names]
                if samples:
                    m = Metric(metric.name, metric.documentation, metric.type)
                    m.samples = samples
                    metrics.append(m)

        class RestrictedRegistry(object):
            def collect(self):
                return metrics

        return RestrictedRegistry()

    def get_sample_value(self, name, labels=None):
        '''Returns the sample value, or None if not found.

        This is inefficient, and intended only for use in unittests.
        '''
        if labels is None:
            labels = {}
        for metric in self.collect():
            for s in metric.samples:
                if s.name == name and s.labels == labels:
                    return s.value
        return None


REGISTRY = CollectorRegistry(auto_describe=True)
'''The default registry.'''

_METRIC_TYPES = (
    'counter', 'gauge', 'summary', 'histogram',
    'gaugehistogram', 'unknown', 'info', 'stateset',
)


class Metric(object):
    '''A single metric family and its samples.

    This is intended only for internal use by the instrumentation client.

    Custom collectors should use GaugeMetricFamily, CounterMetricFamily
    and SummaryMetricFamily instead.
    '''

    def __init__(self, name, documentation, typ, unit=''):
        if unit and not name.endswith("_" + unit):
            name += "_" + unit
        if not _METRIC_NAME_RE.match(name):
            raise ValueError('Invalid metric name: ' + name)
        self.name = name
        self.documentation = documentation
        self.unit = unit
        if typ == 'untyped':
            typ = 'unknown'
        if typ not in _METRIC_TYPES:
            raise ValueError('Invalid metric type: ' + typ)
        self.type = typ
        self.samples = []

    def add_sample(self, name, labels, value, timestamp=None, exemplar=None):
        '''Add a sample to the metric.

        Internal-only, do not use.'''
        self.samples.append(Sample(name, labels, value, timestamp, exemplar))

    def __eq__(self, other):
        return (isinstance(other, Metric) and
                self.name == other.name and
                self.documentation == other.documentation and
                self.type == other.type and
                self.unit == other.unit and
                self.samples == other.samples)

    def __repr__(self):
        return "Metric(%s, %s, %s, %s, %s)" % (
            self.name,
            self.documentation,
            self.type,
            self.unit,
            self.samples,
        )


class UnknownMetricFamily(Metric):
    '''A single unknwon metric and its samples.
    For use by custom collectors.
    '''

    def __init__(self, name, documentation, value=None, labels=None, unit=''):
        Metric.__init__(self, name, documentation, 'unknown', unit)
        if labels is not None and value is not None:
            raise ValueError('Can only specify at most one of value and labels.')
        if labels is None:
            labels = []
        self._labelnames = tuple(labels)
        if value is not None:
            self.add_metric([], value)

    def add_metric(self, labels, value, timestamp=None):
        '''Add a metric to the metric family.
        Args:
        labels: A list of label values
        value: The value of the metric.
        '''
        self.samples.append(Sample(self.name, dict(zip(self._labelnames, labels)), value, timestamp))


# For backward compatibility.
UntypedMetricFamily = UnknownMetricFamily


class CounterMetricFamily(Metric):
    '''A single counter and its samples.

    For use by custom collectors.
    '''

    def __init__(self, name, documentation, value=None, labels=None, created=None, unit=''):
        # Glue code for pre-OpenMetrics metrics.
        if name.endswith('_total'):
            name = name[:-6]
        Metric.__init__(self, name, documentation, 'counter', unit)
        if labels is not None and value is not None:
            raise ValueError('Can only specify at most one of value and labels.')
        if labels is None:
            labels = []
        self._labelnames = tuple(labels)
        if value is not None:
            self.add_metric([], value, created)

    def add_metric(self, labels, value, created=None, timestamp=None):
        '''Add a metric to the metric family.

        Args:
          labels: A list of label values
          value: The value of the metric
          created: Optional unix timestamp the child was created at.
        '''
        self.samples.append(Sample(self.name + '_total', dict(zip(self._labelnames, labels)), value, timestamp))
        if created is not None:
            self.samples.append(Sample(self.name + '_created', dict(zip(self._labelnames, labels)), created, timestamp))


class GaugeMetricFamily(Metric):
    '''A single gauge and its samples.

    For use by custom collectors.
    '''

    def __init__(self, name, documentation, value=None, labels=None, unit=''):
        Metric.__init__(self, name, documentation, 'gauge', unit)
        if labels is not None and value is not None:
            raise ValueError('Can only specify at most one of value and labels.')
        if labels is None:
            labels = []
        self._labelnames = tuple(labels)
        if value is not None:
            self.add_metric([], value)

    def add_metric(self, labels, value, timestamp=None):
        '''Add a metric to the metric family.

        Args:
          labels: A list of label values
          value: A float
        '''
        self.samples.append(Sample(self.name, dict(zip(self._labelnames, labels)), value, timestamp))


class SummaryMetricFamily(Metric):
    '''A single summary and its samples.

    For use by custom collectors.
    '''

    def __init__(self, name, documentation, count_value=None, sum_value=None, labels=None, unit=''):
        Metric.__init__(self, name, documentation, 'summary', unit)
        if (sum_value is None) != (count_value is None):
            raise ValueError('count_value and sum_value must be provided together.')
        if labels is not None and count_value is not None:
            raise ValueError('Can only specify at most one of value and labels.')
        if labels is None:
            labels = []
        self._labelnames = tuple(labels)
        if count_value is not None:
            self.add_metric([], count_value, sum_value)

    def add_metric(self, labels, count_value, sum_value, timestamp=None):
        '''Add a metric to the metric family.

        Args:
          labels: A list of label values
          count_value: The count value of the metric.
          sum_value: The sum value of the metric.
        '''
        self.samples.append(Sample(self.name + '_count', dict(zip(self._labelnames, labels)), count_value, timestamp))
        self.samples.append(Sample(self.name + '_sum', dict(zip(self._labelnames, labels)), sum_value, timestamp))


class HistogramMetricFamily(Metric):
    '''A single histogram and its samples.

    For use by custom collectors.
    '''

    def __init__(self, name, documentation, buckets=None, sum_value=None, labels=None, unit=''):
        Metric.__init__(self, name, documentation, 'histogram', unit)
        if (sum_value is None) != (buckets is None):
            raise ValueError('buckets and sum_value must be provided together.')
        if labels is not None and buckets is not None:
            raise ValueError('Can only specify at most one of buckets and labels.')
        if labels is None:
            labels = []
        self._labelnames = tuple(labels)
        if buckets is not None:
            self.add_metric([], buckets, sum_value)

    def add_metric(self, labels, buckets, sum_value, timestamp=None):
        '''Add a metric to the metric family.

        Args:
          labels: A list of label values
          buckets: A list of lists.
              Each inner list can be a pair of bucket name and value,
              or a triple of bucket name, value, and exemplar.
              The buckets must be sorted, and +Inf present.
          sum_value: The sum value of the metric.
        '''
        for b in buckets:
            bucket, value = b[:2]
            exemplar = None
            if len(b) == 3:
                exemplar = b[2]
            self.samples.append(Sample(
                self.name + '_bucket',
                dict(list(zip(self._labelnames, labels)) + [('le', bucket)]),
                value,
                timestamp,
                exemplar,
            ))
        # +Inf is last and provides the count value.
        self.samples.extend([
            Sample(self.name + '_count', dict(zip(self._labelnames, labels)), buckets[-1][1], timestamp),
            Sample(self.name + '_sum', dict(zip(self._labelnames, labels)), sum_value, timestamp),
        ])


class GaugeHistogramMetricFamily(Metric):
    '''A single gauge histogram and its samples.

    For use by custom collectors.
    '''

    def __init__(self, name, documentation, buckets=None, gsum_value=None, labels=None, unit=''):
        Metric.__init__(self, name, documentation, 'gaugehistogram', unit)
        if labels is not None and buckets is not None:
            raise ValueError('Can only specify at most one of buckets and labels.')
        if labels is None:
            labels = []
        self._labelnames = tuple(labels)
        if buckets is not None:
            self.add_metric([], buckets, gsum_value)

    def add_metric(self, labels, buckets, gsum_value, timestamp=None):
        '''Add a metric to the metric family.

        Args:
          labels: A list of label values
          buckets: A list of pairs of bucket names and values.
              The buckets must be sorted, and +Inf present.
          gsum_value: The sum value of the metric.
        '''
        for bucket, value in buckets:
            self.samples.append(Sample(
                self.name + '_bucket',
                dict(list(zip(self._labelnames, labels)) + [('le', bucket)]),
                value, timestamp))
        # +Inf is last and provides the count value.
        self.samples.extend([
            Sample(self.name + '_gcount', dict(zip(self._labelnames, labels)), buckets[-1][1], timestamp),
            Sample(self.name + '_gsum', dict(zip(self._labelnames, labels)), gsum_value, timestamp),
        ])


class InfoMetricFamily(Metric):
    '''A single info and its samples.

    For use by custom collectors.
    '''

    def __init__(self, name, documentation, value=None, labels=None):
        Metric.__init__(self, name, documentation, 'info')
        if labels is not None and value is not None:
            raise ValueError('Can only specify at most one of value and labels.')
        if labels is None:
            labels = []
        self._labelnames = tuple(labels)
        if value is not None:
            self.add_metric([], value)

    def add_metric(self, labels, value, timestamp=None):
        '''Add a metric to the metric family.

        Args:
          labels: A list of label values
          value: A dict of labels
        '''
        self.samples.append(Sample(
            self.name + '_info',
            dict(dict(zip(self._labelnames, labels)), **value),
            1,
            timestamp,
        ))


class StateSetMetricFamily(Metric):
    '''A single stateset and its samples.

    For use by custom collectors.
    '''

    def __init__(self, name, documentation, value=None, labels=None):
        Metric.__init__(self, name, documentation, 'stateset')
        if labels is not None and value is not None:
            raise ValueError('Can only specify at most one of value and labels.')
        if labels is None:
            labels = []
        self._labelnames = tuple(labels)
        if value is not None:
            self.add_metric([], value)

    def add_metric(self, labels, value, timestamp=None):
        '''Add a metric to the metric family.

        Args:
          labels: A list of label values
          value: A dict of string state names to booleans
        '''
        labels = tuple(labels)
        for state, enabled in sorted(value.items()):
            v = (1 if enabled else 0)
            self.samples.append(Sample(
                self.name,
                dict(zip(self._labelnames + (self.name,), labels + (state,))),
                v,
                timestamp,
            ))


class _MutexValue(object):
    '''A float protected by a mutex.'''

    _multiprocess = False

    def __init__(self, typ, metric_name, name, labelnames, labelvalues, **kwargs):
        self._value = 0.0
        self._lock = Lock()

    def inc(self, amount):
        with self._lock:
            self._value += amount

    def set(self, value):
        with self._lock:
            self._value = value

    def get(self):
        with self._lock:
            return self._value


# struct.pack_into has atomicity issues because it will temporarily write 0 into
# the mmap, resulting in false reads to 0 when experiencing a lot of writes.
# Using direct assignment solves this issue.
def _pack_double(data, pos, value):
    data[pos:pos + 8] = _pack_double_func(value)


def _pack_integer(data, pos, value):
    data[pos:pos + 4] = _pack_integer_func(value)


class _MmapedDict(object):
    """A dict of doubles, backed by an mmapped file.

    The file starts with a 4 byte int, indicating how much of it is used.
    Then 4 bytes of padding.
    There's then a number of entries, consisting of a 4 byte int which is the
    size of the next field, a utf-8 encoded string key, padding to a 8 byte
    alignment, and then a 8 byte float which is the value.

    Not thread safe.
    """

    def __init__(self, filename, read_mode=False):
        self._f = open(filename, 'rb' if read_mode else 'a+b')
        if os.fstat(self._f.fileno()).st_size == 0:
            self._f.truncate(_INITIAL_MMAP_SIZE)
        self._capacity = os.fstat(self._f.fileno()).st_size
        self._m = mmap.mmap(self._f.fileno(), self._capacity, access=mmap.ACCESS_READ if read_mode else mmap.ACCESS_WRITE)

        self._positions = {}
        self._used = _unpack_integer(self._m, 0)[0]
        if self._used == 0:
            self._used = 8
            _pack_integer(self._m, 0, self._used)
        else:
            if not read_mode:
                for key, _, pos in self._read_all_values():
                    self._positions[key] = pos

    def _init_value(self, key):
        """Initialize a value. Lock must be held by caller."""
        encoded = key.encode('utf-8')
        # Pad to be 8-byte aligned.
        padded = encoded + (b' ' * (8 - (len(encoded) + 4) % 8))
        value = struct.pack('i{0}sd'.format(len(padded)).encode(), len(encoded), padded, 0.0)
        while self._used + len(value) > self._capacity:
            self._capacity *= 2
            self._f.truncate(self._capacity)
            self._m = mmap.mmap(self._f.fileno(), self._capacity)
        self._m[self._used:self._used + len(value)] = value

        # Update how much space we've used.
        self._used += len(value)
        _pack_integer(self._m, 0, self._used)
        self._positions[key] = self._used - 8

    def _read_all_values(self):
        """Yield (key, value, pos). No locking is performed."""

        pos = 8

        # cache variables to local ones and prevent attributes lookup
        # on every loop iteration
        used = self._used
        data = self._m
        unpack_from = struct.unpack_from

        while pos < used:
            encoded_len = _unpack_integer(data, pos)[0]
            pos += 4
            encoded = unpack_from(('%ss' % encoded_len).encode(), data, pos)[0]
            padded_len = encoded_len + (8 - (encoded_len + 4) % 8)
            pos += padded_len
            value = _unpack_double(data, pos)[0]
            yield encoded.decode('utf-8'), value, pos
            pos += 8

    def read_all_values(self):
        """Yield (key, value, pos). No locking is performed."""
        for k, v, _ in self._read_all_values():
            yield k, v

    def read_value(self, key):
        if key not in self._positions:
            self._init_value(key)
        pos = self._positions[key]
        # We assume that reading from an 8 byte aligned value is atomic
        return _unpack_double(self._m, pos)[0]

    def write_value(self, key, value):
        if key not in self._positions:
            self._init_value(key)
        pos = self._positions[key]
        # We assume that writing to an 8 byte aligned value is atomic
        _pack_double(self._m, pos, value)

    def close(self):
        if self._f:
            self._m.close()
            self._m = None
            self._f.close()
            self._f = None


def _mmap_key(metric_name, name, labelnames, labelvalues):
    """Format a key for use in the mmap file."""
    # ensure labels are in consistent order for identity
    labels = dict(zip(labelnames, labelvalues))
    return json.dumps([metric_name, name, labels], sort_keys=True)


def _MultiProcessValue(_pidFunc=os.getpid):
    files = {}
    values = []
    pid = {'value': _pidFunc()}
    # Use a single global lock when in multi-processing mode
    # as we presume this means there is no threading going on.
    # This avoids the need to also have mutexes in __MmapDict.
    lock = Lock()

    class _MmapedValue(object):
        '''A float protected by a mutex backed by a per-process mmaped file.'''

        _multiprocess = True

        def __init__(self, typ, metric_name, name, labelnames, labelvalues, multiprocess_mode='', **kwargs):
            self._params = typ, metric_name, name, labelnames, labelvalues, multiprocess_mode
            with lock:
                self.__reset()
                values.append(self)

        def __reset(self):
            typ, metric_name, name, labelnames, labelvalues, multiprocess_mode = self._params
            if typ == 'gauge':
                file_prefix = typ + '_' + multiprocess_mode
            else:
                file_prefix = typ
            if file_prefix not in files:
                filename = os.path.join(
                    os.environ['prometheus_multiproc_dir'],
                    '{0}_{1}.db'.format(file_prefix, pid['value']))
                files[file_prefix] = _MmapedDict(filename)
            self._file = files[file_prefix]
            self._key = _mmap_key(metric_name, name, labelnames, labelvalues)
            self._value = self._file.read_value(self._key)

        def __check_for_pid_change(self):
            actual_pid = _pidFunc()
            if pid['value'] != actual_pid:
                pid['value'] = actual_pid
                # There has been a fork(), reset all the values.
                for f in files.values():
                    f.close()
                files.clear()
                for value in values:
                    value.__reset()

        def inc(self, amount):
            with lock:
                self.__check_for_pid_change()
                self._value += amount
                self._file.write_value(self._key, self._value)

        def set(self, value):
            with lock:
                self.__check_for_pid_change()
                self._value = value
                self._file.write_value(self._key, self._value)

        def get(self):
            with lock:
                self.__check_for_pid_change()
                return self._value

    return _MmapedValue


# Should we enable multi-process mode?
# This needs to be chosen before the first metric is constructed,
# and as that may be in some arbitrary library the user/admin has
# no control over we use an environment variable.
if 'prometheus_multiproc_dir' in os.environ:
    _ValueClass = _MultiProcessValue()
else:
    _ValueClass = _MutexValue


class _LabelWrapper(object):
    '''Handles labels for the wrapped metric.'''

    def __init__(self, wrappedClass, name, labelnames, **kwargs):
        self._wrappedClass = wrappedClass
        self._type = wrappedClass._type
        self._name = name
        self._labelnames = labelnames
        self._kwargs = kwargs
        self._lock = Lock()
        self._metrics = {}

        for l in labelnames:
            if l.startswith('__'):
                raise ValueError('Invalid label metric name: ' + l)

    def labels(self, *labelvalues, **labelkwargs):
        '''Return the child for the given labelset.

        All metrics can have labels, allowing grouping of related time series.
        Taking a counter as an example:

            from prometheus_client import Counter

            c = Counter('my_requests_total', 'HTTP Failures', ['method', 'endpoint'])
            c.labels('get', '/').inc()
            c.labels('post', '/submit').inc()

        Labels can also be provided as keyword arguments:

            from prometheus_client import Counter

            c = Counter('my_requests_total', 'HTTP Failures', ['method', 'endpoint'])
            c.labels(method='get', endpoint='/').inc()
            c.labels(method='post', endpoint='/submit').inc()

        See the best practices on [naming](http://prometheus.io/docs/practices/naming/)
        and [labels](http://prometheus.io/docs/practices/instrumentation/#use-labels).
        '''
        if labelvalues and labelkwargs:
            raise ValueError("Can't pass both *args and **kwargs")

        if labelkwargs:
            if sorted(labelkwargs) != sorted(self._labelnames):
                raise ValueError('Incorrect label names')
            labelvalues = tuple(unicode(labelkwargs[l]) for l in self._labelnames)
        else:
            if len(labelvalues) != len(self._labelnames):
                raise ValueError('Incorrect label count')
            labelvalues = tuple(unicode(l) for l in labelvalues)
        with self._lock:
            if labelvalues not in self._metrics:
                self._metrics[labelvalues] = self._wrappedClass(
                    self._name,
                    self._labelnames,
                    labelvalues,
                    **self._kwargs
                )
            return self._metrics[labelvalues]

    def remove(self, *labelvalues):
        '''Remove the given labelset from the metric.'''
        if len(labelvalues) != len(self._labelnames):
            raise ValueError('Incorrect label count')
        labelvalues = tuple(unicode(l) for l in labelvalues)
        with self._lock:
            del self._metrics[labelvalues]

    def _samples(self):
        with self._lock:
            metrics = self._metrics.copy()
        for labels, metric in metrics.items():
            series_labels = list(zip(self._labelnames, labels))
            for suffix, sample_labels, value in metric._samples():
                yield (suffix, dict(series_labels + list(sample_labels.items())), value)


def _MetricWrapper(cls):
    '''Provides common functionality for metrics.'''

    def init(name, documentation, labelnames=(), namespace='', subsystem='', unit='', registry=REGISTRY, **kwargs):
        full_name = ''
        if namespace:
            full_name += namespace + '_'
        if subsystem:
            full_name += subsystem + '_'
        full_name += name

        if unit and not full_name.endswith("_" + unit):
            full_name += "_" + unit
        if unit and cls._type in ('info', 'stateset'):
            raise ValueError('Metric name is of a type that cannot have a unit: ' + full_name)

        if cls._type == 'counter' and full_name.endswith('_total'):
            full_name = full_name[:-6]  # Munge to OpenMetrics.

        if labelnames:
            labelnames = tuple(labelnames)
            for l in labelnames:
                if not _METRIC_LABEL_NAME_RE.match(l):
                    raise ValueError('Invalid label metric name: ' + l)
                if _RESERVED_METRIC_LABEL_NAME_RE.match(l):
                    raise ValueError('Reserved label metric name: ' + l)
                if l in cls._reserved_labelnames:
                    raise ValueError('Reserved label metric name: ' + l)
            collector = _LabelWrapper(cls, full_name, labelnames, **kwargs)
        else:
            collector = cls(full_name, (), (), **kwargs)

        if not _METRIC_NAME_RE.match(full_name):
            raise ValueError('Invalid metric name: ' + full_name)

        def describe():
            return [Metric(full_name, documentation, cls._type)]

        collector.describe = describe

        def collect():
            metric = Metric(full_name, documentation, cls._type, unit)
            for suffix, labels, value in collector._samples():
                metric.add_sample(full_name + suffix, labels, value)
            return [metric]

        collector.collect = collect

        if registry:
            registry.register(collector)
        return collector

    init.__wrapped__ = cls
    return init


@_MetricWrapper
class Counter(object):
    '''A Counter tracks counts of events or running totals.

    Example use cases for Counters:
    - Number of requests processed
    - Number of items that were inserted into a queue
    - Total amount of data that a system has processed

    Counters can only go up (and be reset when the process restarts). If your use case can go down,
    you should use a Gauge instead.

    An example for a Counter:

        from prometheus_client import Counter

        c = Counter('my_failures_total', 'Description of counter')
        c.inc()     # Increment by 1
        c.inc(1.6)  # Increment by given value

    There are utilities to count exceptions raised:

        @c.count_exceptions()
        def f():
            pass

        with c.count_exceptions():
            pass

        # Count only one type of exception
        with c.count_exceptions(ValueError):
            pass
    '''
    _type = 'counter'
    _reserved_labelnames = []

    def __init__(self, name, labelnames, labelvalues):
        if name.endswith('_total'):
            name = name[:-6]
        self._value = _ValueClass(self._type, name, name + '_total', labelnames, labelvalues)
        self._created = time.time()

    def inc(self, amount=1):
        '''Increment counter by the given amount.'''
        if amount < 0:
            raise ValueError('Counters can only be incremented by non-negative amounts.')
        self._value.inc(amount)

    def count_exceptions(self, exception=Exception):
        '''Count exceptions in a block of code or function.

        Can be used as a function decorator or context manager.
        Increments the counter when an exception of the given
        type is raised up out of the code.
        '''
        return _ExceptionCounter(self, exception)

    def _samples(self):
        return (
            ('_total', {}, self._value.get()),
            ('_created', {}, self._created),
        )


@_MetricWrapper
class Gauge(object):
    '''Gauge metric, to report instantaneous values.

     Examples of Gauges include:
        - Inprogress requests
        - Number of items in a queue
        - Free memory
        - Total memory
        - Temperature

     Gauges can go both up and down.

        from prometheus_client import Gauge

        g = Gauge('my_inprogress_requests', 'Description of gauge')
        g.inc()      # Increment by 1
        g.dec(10)    # Decrement by given value
        g.set(4.2)   # Set to a given value

     There are utilities for common use cases:

        g.set_to_current_time()   # Set to current unixtime

        # Increment when entered, decrement when exited.
        @g.track_inprogress()
        def f():
            pass

        with g.track_inprogress():
            pass

     A Gauge can also take its value from a callback:

        d = Gauge('data_objects', 'Number of objects')
        my_dict = {}
        d.set_function(lambda: len(my_dict))
    '''
    _type = 'gauge'
    _reserved_labelnames = []
    _MULTIPROC_MODES = frozenset(('min', 'max', 'livesum', 'liveall', 'all'))

    def __init__(self, name, labelnames, labelvalues, multiprocess_mode='all'):
        if (_ValueClass._multiprocess and
                multiprocess_mode not in self._MULTIPROC_MODES):
            raise ValueError('Invalid multiprocess mode: ' + multiprocess_mode)
        self._value = _ValueClass(
            self._type, name, name, labelnames, labelvalues,
            multiprocess_mode=multiprocess_mode)

    def inc(self, amount=1):
        '''Increment gauge by the given amount.'''
        self._value.inc(amount)

    def dec(self, amount=1):
        '''Decrement gauge by the given amount.'''
        self._value.inc(-amount)

    def set(self, value):
        '''Set gauge to the given value.'''
        self._value.set(float(value))

    def set_to_current_time(self):
        '''Set gauge to the current unixtime.'''
        self.set(time.time())

    def track_inprogress(self):
        '''Track inprogress blocks of code or functions.

        Can be used as a function decorator or context manager.
        Increments the gauge when the code is entered,
        and decrements when it is exited.
        '''
        return _InprogressTracker(self)

    def time(self):
        '''Time a block of code or function, and set the duration in seconds.

        Can be used as a function decorator or context manager.
        '''
        return _Timer(self.set)

    def set_function(self, f):
        '''Call the provided function to return the Gauge value.

        The function must return a float, and may be called from
        multiple threads. All other methods of the Gauge become NOOPs.
        '''

        def samples(self):
            return (('', {}, float(f())),)

        self._samples = types.MethodType(samples, self)

    def _samples(self):
        return (('', {}, self._value.get()),)


@_MetricWrapper
class Summary(object):
    '''A Summary tracks the size and number of events.

    Example use cases for Summaries:
    - Response latency
    - Request size

    Example for a Summary:

        from prometheus_client import Summary

        s = Summary('request_size_bytes', 'Request size (bytes)')
        s.observe(512)  # Observe 512 (bytes)

    Example for a Summary using time:

        from prometheus_client import Summary

        REQUEST_TIME = Summary('response_latency_seconds', 'Response latency (seconds)')

        @REQUEST_TIME.time()
        def create_response(request):
          """A dummy function"""
          time.sleep(1)

    Example for using the same Summary object as a context manager:

        with REQUEST_TIME.time():
            pass  # Logic to be timed
    '''
    _type = 'summary'
    _reserved_labelnames = ['quantile']

    def __init__(self, name, labelnames, labelvalues):
        self._count = _ValueClass(self._type, name, name + '_count', labelnames, labelvalues)
        self._sum = _ValueClass(self._type, name, name + '_sum', labelnames, labelvalues)
        self._created = time.time()

    def observe(self, amount):
        '''Observe the given amount.'''
        self._count.inc(1)
        self._sum.inc(amount)

    def time(self):
        '''Time a block of code or function, and observe the duration in seconds.

        Can be used as a function decorator or context manager.
        '''
        return _Timer(self.observe)

    def _samples(self):
        return (
            ('_count', {}, self._count.get()),
            ('_sum', {}, self._sum.get()),
            ('_created', {}, self._created))


def _floatToGoString(d):
    if d == _INF:
        return '+Inf'
    elif d == _MINUS_INF:
        return '-Inf'
    elif math.isnan(d):
        return 'NaN'
    else:
        return repr(float(d))


@_MetricWrapper
class Histogram(object):
    '''A Histogram tracks the size and number of events in buckets.

    You can use Histograms for aggregatable calculation of quantiles.

    Example use cases:
    - Response latency
    - Request size

    Example for a Histogram:

        from prometheus_client import Histogram

        h = Histogram('request_size_bytes', 'Request size (bytes)')
        h.observe(512)  # Observe 512 (bytes)

    Example for a Histogram using time:

        from prometheus_client import Histogram

        REQUEST_TIME = Histogram('response_latency_seconds', 'Response latency (seconds)')

        @REQUEST_TIME.time()
        def create_response(request):
          """A dummy function"""
          time.sleep(1)

    Example of using the same Histogram object as a context manager:

        with REQUEST_TIME.time():
            pass  # Logic to be timed

    The default buckets are intended to cover a typical web/rpc request from milliseconds to seconds.
    They can be overridden by passing `buckets` keyword argument to `Histogram`.
    '''
    _type = 'histogram'
    _reserved_labelnames = ['le']

    def __init__(self, name, labelnames, labelvalues, buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, _INF)):
        self._created = time.time()
        self._sum = _ValueClass(self._type, name, name + '_sum', labelnames, labelvalues)
        buckets = [float(b) for b in buckets]
        if buckets != sorted(buckets):
            # This is probably an error on the part of the user,
            # so raise rather than sorting for them.
            raise ValueError('Buckets not in sorted order')
        if buckets and buckets[-1] != _INF:
            buckets.append(_INF)
        if len(buckets) < 2:
            raise ValueError('Must have at least two buckets')
        self._upper_bounds = buckets
        self._buckets = []
        bucket_labelnames = labelnames + ('le',)
        for b in buckets:
            self._buckets.append(_ValueClass(
                self._type,
                name,
                name + '_bucket',
                bucket_labelnames,
                labelvalues + (_floatToGoString(b),),
            ))

    def observe(self, amount):
        '''Observe the given amount.'''
        self._sum.inc(amount)
        for i, bound in enumerate(self._upper_bounds):
            if amount <= bound:
                self._buckets[i].inc(1)
                break

    def time(self):
        '''Time a block of code or function, and observe the duration in seconds.

        Can be used as a function decorator or context manager.
        '''
        return _Timer(self.observe)

    def _samples(self):
        samples = []
        acc = 0
        for i, bound in enumerate(self._upper_bounds):
            acc += self._buckets[i].get()
            samples.append(('_bucket', {'le': _floatToGoString(bound)}, acc))
        samples.append(('_count', {}, acc))
        samples.append(('_sum', {}, self._sum.get()))
        samples.append(('_created', {}, self._created))
        return tuple(samples)


@_MetricWrapper
class Info(object):
    '''Info metric, key-value pairs.

     Examples of Info include:
        - Build information
        - Version information
        - Potential target metadata

     Example usage:
        from prometheus_client import Info

        i = Info('my_build', 'Description of info')
        i.info({'version': '1.2.3', 'buildhost': 'foo@bar'})

     Info metrics do not work in multiprocess mode.
    '''
    _type = 'info'
    _reserved_labelnames = []

    def __init__(self, name, labelnames, labelvalues):
        self._labelnames = set(labelnames)
        self._lock = Lock()
        self._value = {}

    def info(self, val):
        '''Set info metric.'''
        if self._labelnames.intersection(val.keys()):
            raise ValueError('Overlapping labels for Info metric, metric: %s child: %s' % (
                self._labelnames, val))
        with self._lock:
            self._value = dict(val)

    def _samples(self):
        with self._lock:
            return (('_info', self._value, 1.0,),)


@_MetricWrapper
class Enum(object):
    '''Enum metric, which of a set of states is true.

     Example usage:
        from prometheus_client import Enum

        e = Enum('task_state', 'Description of enum',
          states=['starting', 'running', 'stopped'])
        e.state('running')

     The first listed state will be the default.
     Enum metrics do not work in multiprocess mode.
    '''
    _type = 'stateset'
    _reserved_labelnames = []

    def __init__(self, name, labelnames, labelvalues, states=None):
        if name in labelnames:
            raise ValueError('Overlapping labels for Enum metric: %s' % (name,))
        if not states:
            raise ValueError('No states provided for Enum metric: %s' % (name,))
        self._name = name
        self._states = states
        self._value = 0
        self._lock = Lock()

    def state(self, state):
        '''Set enum metric state.'''
        with self._lock:
            self._value = self._states.index(state)

    def _samples(self):
        with self._lock:
            return [
                ('', {self._name: s}, 1 if i == self._value else 0,)
                for i, s
                in enumerate(self._states)
            ]


class _ExceptionCounter(object):
    def __init__(self, counter, exception):
        self._counter = counter
        self._exception = exception

    def __enter__(self):
        pass

    def __exit__(self, typ, value, traceback):
        if isinstance(value, self._exception):
            self._counter.inc()

    def __call__(self, f):
        def wrapped(func, *args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return decorate(f, wrapped)


class _InprogressTracker(object):
    def __init__(self, gauge):
        self._gauge = gauge

    def __enter__(self):
        self._gauge.inc()

    def __exit__(self, typ, value, traceback):
        self._gauge.dec()

    def __call__(self, f):
        def wrapped(func, *args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return decorate(f, wrapped)


class _Timer(object):
    def __init__(self, callback):
        self._callback = callback

    def _new_timer(self):
        return self.__class__(self._callback)

    def __enter__(self):
        self._start = default_timer()

    def __exit__(self, typ, value, traceback):
        # Time can go backwards.
        duration = max(default_timer() - self._start, 0)
        self._callback(duration)

    def __call__(self, f):
        def wrapped(func, *args, **kwargs):
            # Obtaining new instance of timer every time
            # ensures thread safety and reentrancy.
            with self._new_timer():
                return func(*args, **kwargs)

        return decorate(f, wrapped)
